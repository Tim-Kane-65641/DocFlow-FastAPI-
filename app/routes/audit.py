from fastapi import APIRouter, Depends
from app.schemas import AuditOut
from app.core.auth import require_role, CurrentUser
from app.main import db

router = APIRouter(tags=["Audit"])

@router.get("/v1/audit", response_model=list[AuditOut])
async def audit_log(user: CurrentUser = Depends(require_role(["admin","support","moderator"]))):
    cursor = db.audit_logs.find({}).sort("at", -1).limit(200)
    out = []
    async for row in cursor:
        out.append({
            "_id": row["_id"],
            "at": row["at"],
            "userId": row.get("userId"),
            "action": row["action"],
            "entityType": row["entityType"],
            "entityId": row.get("entityId"),
            "metadata": row.get("metadata"),
        })
    return out