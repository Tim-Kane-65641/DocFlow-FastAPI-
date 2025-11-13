from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.schemas import OCRIn, OCRResp
from app.core.auth import require_role, write_guard, CurrentUser
from app.core.utils import classify_text, extract_unsubscribe, can_create_task_today, new_id, log_audit
from app.db import get_db
db = get_db()

router = APIRouter(tags=["OCR"])

@router.post("/v1/webhooks/ocr", response_model=OCRResp)
async def ocr_webhook(payload: OCRIn, user: CurrentUser = Depends(require_role(["admin","user","support","moderator"]))):
    write_guard(user)
    if not (payload.source and payload.imageId and payload.text):
        raise HTTPException(400, 'source,imageId,text required')

    cls = classify_text(payload.text)
    await log_audit(user.id, 'webhook.ocr.ingest', 'WebhookEvent', payload.imageId, {"source": payload.source, "cls": cls})

    task = None
    if cls == 'ad':
        unsub = extract_unsubscribe(payload.text)
        if unsub and await can_create_task_today(user.id, payload.source):
            task = {"_id": new_id(), "user_id": user.id, "status": 'pending', "channel": unsub['channel'], "target": unsub['target'], "source": payload.source, "at": datetime.utcnow()}
            await db.tasks.insert_one(task)
            await log_audit(user.id, 'task.create', 'Task', task["_id"], {"channel": task['channel'], "target": task['target'], "source": payload.source})
            task = {"id": task["_id"], "channel": task["channel"], "target": task["target"]}

    return OCRResp(classification=cls, task_created=bool(task), task=task)