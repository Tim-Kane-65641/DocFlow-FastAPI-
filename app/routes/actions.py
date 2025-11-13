from fastapi import APIRouter, Depends, HTTPException
from app.main import db
from app.schemas import ActionRunIn, ActionRunOut
from app.core.auth import require_role, write_guard, CurrentUser
from app.core.utils import mock_processor, new_id, find_or_create_tag, log_audit
from datetime import datetime

router = APIRouter(tags=["Actions"])

@router.post("/v1/actions/run", response_model=ActionRunOut)
async def actions_run(body: ActionRunIn, user: CurrentUser = Depends(require_role(["admin","user","support","moderator"]))):
    write_guard(user)
    scope = body.scope
    if (scope.type == 'folder' and scope.ids) or (scope.type == 'files' and scope.name):
        raise HTTPException(400, 'scope must be either folder or files, not both')

    docs = []
    if scope.type == 'folder':
        if not scope.name:
            raise HTTPException(400, 'scope.name required')
        tag_query = {"name": scope.name}
        if user.role != 'admin':
            tag_query["owner_id"] = user.id
        tag = await db.tags.find_one(tag_query)
        if tag:
            async for link in db.document_tags.find({"tag_id": tag["_id"], "is_primary": True}):
                d = await db.documents.find_one({"_id": link["document_id"]})
                if d and (user.role=='admin' or d["owner_id"]==user.id):
                    docs.append(d)
    else:
        for i in scope.ids or []:
            d = await db.documents.find_one({"_id": i})
            if d and (user.role=='admin' or d["owner_id"]==user.id):
                docs.append(d)

    context = [{"id": d["_id"], "title": d["filename"], "sample": (d.get("text_content","")[:200])} for d in docs]
    processed = await mock_processor(scope.dict(), context)

    created = []
    if 'make_document' in body.actions:
        gen = {
            "_id": new_id(), "owner_id": user.id, "filename": f"generated_{int(datetime.utcnow().timestamp())}.md",
            "mime": "text/markdown", "text_content": processed['text'], "created_at": datetime.utcnow()
        }
        await db.documents.insert_one(gen)
        gtag = await find_or_create_tag(user.id, 'generated')
        await db.document_tags.insert_one({"_id": new_id(), "document_id": gen["_id"], "tag_id": gtag["_id"], "is_primary": True})
        created.append({"type":"document","id": gen["_id"]})

    if 'make_csv' in body.actions:
        csvdoc = {
            "_id": new_id(), "owner_id": user.id, "filename": f"result_{int(datetime.utcnow().timestamp())}.csv",
            "mime": "text/csv", "text_content": processed['csv'], "created_at": datetime.utcnow()
        }
        await db.documents.insert_one(csvdoc)
        gtag = await find_or_create_tag(user.id, 'generated')
        await db.document_tags.insert_one({"_id": new_id(), "document_id": csvdoc["_id"], "tag_id": gtag["_id"], "is_primary": True})
        created.append({"type":"csv","id": csvdoc["_id"]})

    # usage credits (5)
    await db.usages.insert_one({"_id": new_id(), "user_id": user.id, "credits": 5, "at": datetime.utcnow(), "kind": "actions_run"})
    await log_audit(user.id, 'actions.run', 'Action', None, {"scope": scope.dict(), "created": created})

    return ActionRunOut(created=created, credits_charged=5)

@router.get("/v1/actions/usage/month")
async def usage_month(user: CurrentUser = Depends(require_role(["admin","user","support","moderator"]))):
    from datetime import datetime
    key = datetime.utcnow().strftime('%Y-%m')
    # query all usage in month for this user (or all when admin)
    cursor = db.usages.find({"kind":"actions_run"})
    total = 0
    async for u in cursor:
        if user.role != 'admin' and u.get('user_id') != user.id:
            continue
        if u['at'].strftime('%Y-%m') == key:
            total += u.get('credits', 0)
    return {"month": key, "credits": total}