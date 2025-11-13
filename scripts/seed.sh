#!/usr/bin/env bash
python - <<'PY'
from app.utils import new_id
from datetime import datetime
import asyncio
from app.db import get_db
db = get_db()

async def seed():
    uid = "u_demo"
    invoices = {"_id": new_id(), "name": "invoices-2025", "owner_id": uid, "created_at": datetime.utcnow()}
    letters = {"_id": new_id(), "name": "letters", "owner_id": uid, "created_at": datetime.utcnow()}
    await db.tags.insert_many([invoices, letters])
    d1 = {"_id": new_id(), "owner_id": uid, "filename": "invoice_jan.txt", "mime": "text/plain",
          "text_content": "Invoice #1001 Bank transfer GST", "created_at": datetime.utcnow()}
    d2 = {"_id": new_id(), "owner_id": uid, "filename": "promo_letter.txt", "mime": "text/plain",
          "text_content": "Limited time SALE unsubscribe: mailto:stop@brand.com", "created_at": datetime.utcnow()}
    await db.documents.insert_many([d1, d2])
    await db.document_tags.insert_many([
        {"_id": new_id(), "document_id": d1["_id"], "tag_id": invoices["_id"], "is_primary": True},
        {"_id": new_id(), "document_id": d2["_id"], "tag_id": letters["_id"], "is_primary": True},
    ])
    print("Seed complete")

asyncio.run(seed())
PY
