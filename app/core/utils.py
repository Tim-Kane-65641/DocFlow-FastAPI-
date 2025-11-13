import re
import uuid
from datetime import datetime
from typing import Optional
from app.db import db

FINANCIAL_TERMS = ['invoice','statement','bank','legal','court','tax','gst','pan','account']
PROMO_TERMS = ['sale','discount','offer','deal','promo','unsubscribe','limited time']

# IDs

def new_id() -> str:
    return str(uuid.uuid4())

# Audit
async def log_audit(user_id: Optional[str], action: str, entity_type: str, entity_id: Optional[str], metadata: Optional[dict] = None):
    entry = {
        "_id": new_id(),
        "at": datetime.utcnow(),
        "userId": user_id,
        "action": action,
        "entityType": entity_type,
        "entityId": entity_id,
        "metadata": metadata,
    }
    await db.audit_logs.insert_one(entry)

# Tags
async def find_or_create_tag(owner_id: str, name: str) -> dict:
    tag = await db.tags.find_one({"owner_id": owner_id, "name": name})
    if tag:
        return tag
    tag = {"_id": new_id(), "name": name, "owner_id": owner_id, "created_at": datetime.utcnow()}
    await db.tags.insert_one(tag)
    return tag

# naive search
def naive_match(text: str, q: str) -> bool:
    text = text or ""
    return q.lower() in text.lower()

# actions processor
async def mock_processor(scope: dict, context: list[dict]) -> dict:
    titles = ", ".join([c["title"] for c in context])
    seed = sum(len(c["sample"]) for c in context)
    summary = f"Scope={scope['type']}{(':'+scope['name']) if scope.get('name') else ''}; Docs={len(context)}; Titles=[{titles}]"
    text_out = f"# Generated Summary\n{summary}\nSeed={seed}"
    # CSV rows
    rows = ["doc_id,title,sample_len"]
    for c in context:
        title = c["title"].replace("\\", "\\\\").replace('"', '""')
        rows.append(f'{c["id"]},"{title}",{len(c["sample"])})')
    csv_out = "\n".join(rows) + "\n"
    return {"text": text_out, "csv": csv_out}

# classification
def classify_text(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in FINANCIAL_TERMS):
        return 'official'
    if any(w in t for w in PROMO_TERMS):
        return 'ad'
    return 'unknown'

# unsubscribe extraction

def extract_unsubscribe(text: str) -> Optional[dict]:
    m = re.search(r'mailto:([^\s>]+)', text, flags=re.I)
    if m:
        return {"channel":"email","target":m.group(1)}
    m = re.search(r'https?://[^\s>]+', text, flags=re.I)
    if m:
        return {"channel":"url","target":m.group(0)}
    m = re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', text, flags=re.I)
    if m:
        return {"channel":"email","target":m.group(0)}
    return None

# rate limit: max 3 tasks/day/source/user
async def can_create_task_today(user_id: str, source: str) -> bool:
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count = await db.tasks.count_documents({
        "user_id": user_id,
        "source": source,
        "at": {"$gte": start}
    })
    return count < 3