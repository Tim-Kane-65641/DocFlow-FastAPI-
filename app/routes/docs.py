from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from datetime import datetime
from app.schemas import DocOut, SearchOut
from app.core.auth import require_role, write_guard, CurrentUser
from app.main import db
from app.core.utils import new_id, find_or_create_tag, log_audit, naive_match

router = APIRouter(tags=["Documents"])

@router.post("/v1/docs", response_model=DocOut)
async def upload_doc(
    primaryTag: str = Form(...),
    secondaryTags: list[str] = Form([]),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role(["admin","user","support","moderator"]))
):
    write_guard(user)
    content = (await file.read()).decode(errors="ignore")

    # ensure primary tag
    ptag = await find_or_create_tag(user.id, primaryTag)

    # create doc
    doc = {
        "_id": new_id(),
        "owner_id": user.id,
        "filename": file.filename,
        "mime": file.content_type or "text/plain",
        "text_content": content,
        "created_at": datetime.utcnow(),
    }
    await db.documents.insert_one(doc)

    # link primary
    await db.document_tags.insert_one({
        "_id": new_id(),
        "document_id": doc["_id"],
        "tag_id": ptag["_id"],
        "is_primary": True,
    })

    # link secondary
    for name in secondaryTags:
        if not name or name == primaryTag:
            continue
        t = await find_or_create_tag(user.id, name)
        await db.document_tags.insert_one({
            "_id": new_id(),
            "document_id": doc["_id"],
            "tag_id": t["_id"],
            "is_primary": False,
        })

    await log_audit(user.id, 'document.upload', 'Document', doc["_id"], {"filename": doc["filename"], "primaryTag": primaryTag})
    return DocOut(**doc)

@router.get("/v1/folders")
async def list_folders(user: CurrentUser = Depends(require_role(["admin","user","support","moderator"]))):
    # aggregate primary counts per tag name for this user (or all if admin)
    pipeline = [
        {"$match": {"is_primary": True}},
        {"$lookup": {"from": "documents", "localField": "document_id", "foreignField": "_id", "as": "doc"}},
        {"$unwind": "$doc"},
        # tenant isolation unless admin
        {"$match": ({"doc.owner_id": user.id} if user.role != 'admin' else {})},
        {"$lookup": {"from": "tags", "localField": "tag_id", "foreignField": "_id", "as": "tag"}},
        {"$unwind": "$tag"},
        {"$group": {"_id": "$tag.name", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "name": "$_id", "count": 1}},
    ]
    results = await db.document_tags.aggregate(pipeline).to_list(None)
    return results

@router.get("/v1/folders/{tag}/docs", response_model=list[DocOut])
async def list_docs_in_folder(tag: str, user: CurrentUser = Depends(require_role(["admin","user","support","moderator"]))):
    # find tag(s)
    tag_query = {"name": tag}
    if user.role != 'admin':
        tag_query["owner_id"] = user.id
    tags = await db.tags.find(tag_query).to_list(None)
    if not tags:
        return []
    tag_ids = [t["_id"] for t in tags]

    # find primary doc links
    links = await db.document_tags.find({"tag_id": {"$in": tag_ids}, "is_primary": True}).to_list(None)
    doc_ids = [link["document_id"] for link in links]

    # fetch documents with tenant isolation
    doc_query = {"_id": {"$in": doc_ids}}
    if user.role != 'admin':
        doc_query["owner_id"] = user.id
    docs = await db.documents.find(doc_query).to_list(None)

    return [DocOut(**d) for d in docs]


@router.get("/v1/search", response_model=SearchOut)
async def search(q: str, scope: str, name: str | None = None, ids: list[str] | None = Query(default=None),
                 user: CurrentUser = Depends(require_role(["admin","user","support","moderator"]))):
    if scope not in {"folder","files"}:
        raise HTTPException(400, "scope must be either 'folder' or 'files'")
    if (scope == "folder" and ids) or (scope == "files" and name):
        raise HTTPException(400, "scope must be either folder or files, not both")

    candidates = []
    if scope == "folder":
        if not name:
            raise HTTPException(400, "Folder name required for folder scope")
        tag_query = {"name": name}
        if user.role != 'admin':
            tag_query["owner_id"] = user.id
        tag = await db.tags.find_one(tag_query)
        if not tag:
            return SearchOut(count=0, results=[])
        # primary links for that tag
        links = db.document_tags.find({"tag_id": tag["_id"], "is_primary": True})
        async for link in links:
            doc = await db.documents.find_one({"_id": link["document_id"]})
            if doc and (user.role=='admin' or doc["owner_id"]==user.id):
                candidates.append(doc)
    else:
        for i in ids or []:
            doc = await db.documents.find_one({"_id": i})
            if doc and (user.role=='admin' or doc["owner_id"]==user.id):
                candidates.append(doc)

    results = [DocOut(**d) for d in candidates if naive_match(f"{d['text_content']} {d['filename']}", q)]
    return SearchOut(count=len(results), results=results)