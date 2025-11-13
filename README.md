# 📄 DocFlow – FastAPI + MongoDB Backend

A small backend service that demonstrates how to manage **documents, folders, and tags**,  
run **scoped actions** (like generating CSVs), handle **OCR ingestion webhooks**,  
and support **RBAC, auditing, and metrics** — all in one place.

Built with **FastAPI**, **MongoDB (Motor)**, and a pinch of mock AI processing.

---

## 🧩 Features

- Document upload with **primary + secondary tags**
- Folder and file–scoped **search**
- Scoped **agent actions** (`make_csv`, `make_document`)
- OCR webhook for **classification** + **task creation**
- Role-based access control (**admin, user, moderator, support**)
- Usage tracking, auditing, and metrics APIs
- Dockerized setup with Mongo
- Basic test suite (pytest)

---

## ⚙️ Setup & Run

### 1️⃣ Clone & install

```bash
git clone https://github.com/yourname/docflow.git
cd docflow
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2️⃣ Run with Docker (recommended)

```bash
docker-compose up --build
```

MongoDB will start on `localhost:27017`  
API runs at `http://127.0.0.1:8000`

### 3️⃣ Local dev run

```bash
uvicorn app.main:app --reload
```

Swagger Docs → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔑 Auth

Use a simple **JWT-like mock token** for testing:

```bash
User Token:
Authorization: Bearer eyJzdWIiOiJ1X2RlbW8iLCJlbWFpbCI6ImRlbW9AZXhhbXBsZS5jb20iLCJyb2xlIjoidXNlciJ9
Admin Token
Authorization: Bearer eyJzdWIiOiJ1X2RlbW8iLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwicm9sZSI6ImFkbWluIn0=
```

- `admin` can view everything  
- normal `user` can only access their own docs  

---

## 🧠 API Reference (short version)

### 1️⃣ Upload a Document
```bash
curl -X POST "http://127.0.0.1:8000/v1/docs"  -H "Authorization: Bearer <token>"  -F "file=@invoice.txt"  -F "primaryTag=invoices"  -F "secondaryTags=finance"  -F "secondaryTags=tax"
```

### 2️⃣ List Folders
```bash
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/v1/folders
```

### 3️⃣ Search
```bash
curl "http://127.0.0.1:8000/v1/search?q=invoice&scope=files&ids=abc123&ids=xyz789"  -H "Authorization: Bearer <token>"
```

### 4️⃣ Run Scoped Action
```bash
curl -X POST http://127.0.0.1:8000/v1/actions/run  -H "Authorization: Bearer <token>"  -H "Content-Type: application/json"  -d '{
   "scope": {"type":"folder","name":"invoices"},
   "messages":[{"role":"user","content":"make csv"}],
   "actions":["make_csv"]
 }'
```

### 5️⃣ OCR Webhook
```bash
curl -X POST http://127.0.0.1:8000/v1/webhooks/ocr  -H "Authorization: Bearer <token>"  -H "Content-Type: application/json"  -d '{
   "source":"scanner-01",
   "imageId":"img_123",
   "text":"LIMITED TIME SALE unsubscribe: mailto:stop@brand.com",
   "meta":{"address":"123 Main St"}
 }'
```

---

## 🧱 Design Decisions & Tradeoffs

- **MongoDB** chosen for flexible document-tag structure.
- **Motor (async)** driver used, but tests simplified to **sync pytest** for ease.
- **Scoped actions** are deterministic mocks – no actual AI call.
- **JWTs** are mock tokens for demo purposes only.
- **Rate limits** and **credits** are stored per user in Mongo for clarity.

⚖️ Tradeoff: No real file storage or OCR engine, only text-based simulation.

---

## 🧪 Tests

```bash
pytest -v --disable-warnings
```

Covers:
- Folder vs File scope rule  
- Primary tag uniqueness  
- JWT isolation and role enforcement  
- Webhook classification and rate-limiting  
- Credits tracking on scoped actions  

---

## 🚀 What I’d Do Next (with more time)

- Add **real file storage** (S3 or local volume)
- Integrate actual **OpenAI / LangChain** for intelligent processing
- Add proper **JWT verification** and refresh tokens
- Improve **search indexing** (Elasticsearch or Meilisearch)
- Add **simple web dashboard** for browsing folders + metrics

---

## 🕒 Timeline

| Phase | Date | Notes |
|-------|------|-------|
| Start | **Tuesday, Nov 11, 2025** | Setup FastAPI + Mongo, models & auth |
| Mid | **Nov 12–13, 2025** | Implemented OCR webhook, actions, and audit |
| Finish | **Friday, Nov 14, 2025** | Testing, docs, and containerization |

---

## 💬 Author

**Your Name**  
FastAPI backend demo project.  
Feedback and PRs welcome! 🚀
