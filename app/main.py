import base64
from fastapi import FastAPI
from app.db import db
from app.routes import docs, actions, ocr, metrics, audit
from app.core.utils import new_id
from datetime import datetime

app = FastAPI(title="DocFlow — FastAPI + MongoDB")

app.include_router(docs.router)
app.include_router(actions.router)
app.include_router(ocr.router)
app.include_router(metrics.router)
app.include_router(audit.router)

@app.on_event("startup")
async def seed():
    # seed demo user artifacts: tags/docs/links
    if await db.documents.count_documents({}) == 0:
        uid = "u_demo"
        db.users.insert_one({"_id": uid, "email": "demo@example.com", "role": "user", "created_at": datetime.utcnow()})
        db.users.insert_one({"_id": uid, "email": "admin@example.com", "role": "admin", "created_at": datetime.utcnow()})
        invoices = {"_id": new_id(), "name": "invoices-2025", "owner_id": uid, "created_at": datetime.utcnow()}
        letters  = {"_id": new_id(), "name": "letters",        "owner_id": uid, "created_at": datetime.utcnow()}
        await db.tags.insert_many([invoices, letters])
        d1 = {"_id": new_id(), "owner_id": uid, "filename": "invoice_jan.txt", "mime": "text/plain", "text_content": "Invoice #1001 Bank transfer GST", "created_at": datetime.utcnow()}
        d2 = {"_id": new_id(), "owner_id": uid, "filename": "promo_letter.txt", "mime": "text/plain", "text_content": "Limited time SALE unsubscribe: mailto:stop@brand.com", "created_at": datetime.utcnow()}
        await db.documents.insert_many([d1, d2])
        await db.document_tags.insert_many([
            {"_id": new_id(), "document_id": d1["_id"], "tag_id": invoices["_id"], "is_primary": True},
            {"_id": new_id(), "document_id": d2["_id"], "tag_id": letters["_id"],  "is_primary": True},
        ])
    print("Demo token (use as Bearer):", base64.b64encode(b'{"sub":"u_demo","email":"demo@example.com","role":"user"}').decode()) 
    print("Admin token (use as Bearer):", base64.b64encode(b'{"sub":"u_demo","email":"admin@example.com","role":"admin"}').decode())