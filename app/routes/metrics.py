from fastapi import APIRouter, Depends
from datetime import datetime
from app.schemas import MetricsOut
from app.main import db
from app.core.auth import require_role, CurrentUser

router = APIRouter(tags=["Metrics"])

@router.get("/v1/metrics", response_model=MetricsOut)
async def metrics(user: CurrentUser = Depends(require_role(["admin","user","support","moderator"]))):
    # docs total
    docs_filter = {} if user.role=='admin' else {"owner_id": user.id}
    docs_total = await db.documents.count_documents(docs_filter)

    # folders total (unique primary tag names)
    pipeline = [
        {"$match": {"is_primary": True}},
        {"$lookup": {"from": "documents", "localField": "document_id", "foreignField": "_id", "as": "doc"}},
        {"$unwind": "$doc"},
        {"$match": ({} if user.role=='admin' else {"doc.owner_id": user.id})},
        {"$lookup": {"from": "tags", "localField": "tag_id", "foreignField": "_id", "as": "tag"}},
        {"$unwind": "$tag"},
        {"$group": {"_id": "$tag.name"}},
        {"$count": "folders_total"}
    ]
    rows = await db.document_tags.aggregate(pipeline).to_list(None)
    folders_total = rows[0]["folders_total"] if rows else 0

    # actions this month
    key = datetime.utcnow().strftime('%Y-%m')
    actions_month = 0
    async for u in db.usages.find({"kind":"actions_run"}):
        if user.role!='admin' and u.get('user_id')!=user.id:
            continue
        if u['at'].strftime('%Y-%m') == key:
            actions_month += 1

    # tasks today
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tasks_filter = {"at": {"$gte": start}}
    if user.role != 'admin':
        tasks_filter["user_id"] = user.id
    tasks_today = await db.tasks.count_documents(tasks_filter)

    return MetricsOut(docs_total=docs_total, folders_total=folders_total, actions_month=actions_month, tasks_today=tasks_today)