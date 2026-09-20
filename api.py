from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tempfile
import json
from datetime import datetime, timezone

app = FastAPI(title="SHIPWISE API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional Firestore connection.
db = None
firestore_error = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    key_candidates = [
        Path(__file__).parent / "serviceAccountKey.json",
        Path(__file__).parent / "firebase-service-account.json",
    ]

    key = next((p for p in key_candidates if p.exists()), None)

    if key:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(str(key)))
        db = firestore.client()
    else:
        firestore_error = "No Firebase service account key found."
except Exception as e:
    firestore_error = str(e)


@app.get("/")
def root():
    return {
        "service": "SHIPWISE API",
        "status": "running",
        "firestore": db is not None,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "firestore": db is not None,
        "firestore_error": firestore_error,
    }


@app.get("/firestore/status")
def firestore_status():
    if db is None:
        return {
            "connected": False,
            "error": firestore_error,
        }

    try:
        # Lightweight connectivity check.
        list(db.collection("shipwise_results").limit(1).stream())
        return {"connected": True}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.get("/results")
def results(limit: int = 50):
    if db is None:
        return {"results": [], "firestore": False, "error": firestore_error}

    try:
        docs = db.collection("shipwise_results").limit(limit).stream()
        output = []
        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            output.append(item)
        return {"results": output, "firestore": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def save_result(result: dict):
    if db is None:
        return None

    result = dict(result)
    result["processed_at"] = datetime.now(timezone.utc).isoformat()

    ref = db.collection("shipwise_results").document()
    ref.set(result)
    return ref.id


@app.post("/results")
async def create_result(payload: dict):
    doc_id = save_result(payload)
    return {
        "saved": doc_id is not None,
        "id": doc_id,
        "result": payload,
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()

    allowed = {".txt", ".pdf", ".xlsx", ".docx", ".pptx"}
    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {sorted(allowed)}"
        )

    data = await file.read()

    # This endpoint validates upload and stores an intake record.
    # Existing 94.53% classification/extraction logic remains untouched.
    intake = {
        "filename": file.filename,
        "content_type": file.content_type,
        "extension": suffix,
        "size_bytes": len(data),
        "status": "RECEIVED",
    }

    doc_id = save_result(intake)

    return {
        "success": True,
        "message": "Document received.",
        "firestore_saved": doc_id is not None,
        "id": doc_id,
        "file": intake,
    }
