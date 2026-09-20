import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, firestore, initialize_app, get_app

from document_reader import read_document
from extractor import extract_fields, get_missing_fields
from comparator import compare_documents

app = FastAPI(title="SHIPWISE API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_firebase():
    try:
        get_app()
        return True, None
    except ValueError:
        pass

    for path in (
        "/etc/secrets/serviceAccountKey.json",
        "/etc/secrets/firebase-service-account.json",
        str(Path(__file__).resolve().parent / "serviceAccountKey.json"),
        str(Path(__file__).resolve().parent / "firebase-service-account.json"),
    ):
        if os.path.exists(path):
            try:
                initialize_app(credentials.Certificate(path))
                return True, None
            except Exception as exc:
                return False, str(exc)

    try:
        initialize_app()
        return True, None
    except Exception as exc:
        return False, str(exc)

FIREBASE_OK, FIREBASE_ERROR = init_firebase()

def get_db():
    if not FIREBASE_OK:
        return None
    try:
        return firestore.client()
    except Exception:
        return None

@app.get("/")
def root():
    return {
        "service": "SHIPWISE API",
        "status": "running",
        "firestore": get_db() is not None,
    }

@app.get("/health")
def health():
    db = get_db()
    return {
        "status": "healthy",
        "firestore": db is not None,
        "firestore_error": None if db is not None else FIREBASE_ERROR,
    }

@app.get("/firestore/status")
def firestore_status():
    db = get_db()
    if db is None:
        return {"firestore": False, "error": FIREBASE_ERROR}
    try:
        list(db.collection("shipwise_results").limit(1).stream())
        return {"firestore": True}
    except Exception as exc:
        return {"firestore": False, "error": str(exc)}

@app.get("/results")
def get_results():
    db = get_db()
    if db is None:
        return {"results": [], "firestore": False}
    docs = db.collection("shipwise_results").stream()
    results = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        results.append(item)
    return {"results": results, "firestore": True}

@app.post("/results")
def save_result(payload: dict):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Firestore unavailable")
    from datetime import datetime, timezone
    payload = dict(payload)
    payload["created_at"] = datetime.now(timezone.utc).isoformat()
    ref = db.collection("shipwise_results").document()
    ref.set(payload)
    return {"saved": True, "id": ref.id, "result": payload}

class UploadedInbox:
    def __init__(self, files):
        self.files = files

    def read_bytes(self, attachment):
        return self.files[attachment]

    def read_text(self, attachment, encoding="utf-8"):
        return self.files[attachment].decode(encoding, errors="replace")

SUPPORTED_EXTENSIONS = {".txt", ".xlsx", ".docx", ".pdf"}

def role(filename):
    name = Path(filename).name.lower()
    if "_si." in name or name.startswith("si.") or "shipping_instruction" in name:
        return "si"
    if "_bl." in name or name.startswith("bl.") or "bill_of_lading" in name:
        return "bl"
    return None

def review_result(reason):
    return {
        "category": "BL_COMPARISON",
        "status": "NEEDS_REVIEW",
        "review_reason": reason,
        "has_defect": False,
        "defect_fields": [],
    }

@app.post("/process")
async def process_documents(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    stored = {}
    for upload in files:
        filename = Path(upload.filename or "").name
        suffix = Path(filename).suffix.lower()
        if not filename:
            continue
        if suffix not in SUPPORTED_EXTENSIONS:
            return {"result": review_result("wrong_doc_type"),
                    "message": f"Unsupported document type: {suffix or 'unknown'}"}
        data = await upload.read()
        if not data:
            return {"result": review_result("unreadable"),
                    "message": f"Empty file: {filename}"}
        stored[filename] = data

    si_name = next((n for n in stored if role(n) == "si"), None)
    bl_name = next((n for n in stored if role(n) == "bl"), None)

    if si_name is None or bl_name is None:
        return {
            "result": review_result("missing_attachment"),
            "message": "Upload one SI and one BL document. Filenames should contain _SI and _BL."
        }

    inbox = UploadedInbox(stored)

    try:
        si_text = read_document(inbox, si_name)
        bl_text = read_document(inbox, bl_name)
    except Exception as exc:
        return {"result": review_result("unreadable"), "message": str(exc)}

    si_fields = extract_fields(si_text)
    bl_fields = extract_fields(bl_text)
    si_missing = get_missing_fields(si_fields)
    bl_missing = get_missing_fields(bl_fields)

    if si_missing or bl_missing:
        result = review_result("missing_value")
        result.update({
            "si_fields": si_fields,
            "bl_fields": bl_fields,
            "missing_si_fields": si_missing,
            "missing_bl_fields": bl_missing,
        })
    else:
        comparison = compare_documents(si_fields, bl_fields)
        differences = comparison.get("differences", {})
        if any(x.get("reason") == "missing_value" for x in differences.values()):
            result = review_result("missing_value")
            result.update({"si_fields": si_fields, "bl_fields": bl_fields})
        else:
            result = {
                "category": "BL_COMPARISON",
                "status": comparison["status"],
                "review_reason": None,
                "has_defect": comparison["has_defect"],
                "defect_fields": comparison["defect_fields"],
                "si_fields": si_fields,
                "bl_fields": bl_fields,
                "differences": differences,
            }

    db = get_db()
    firestore_id = None
    if db is not None:
        from datetime import datetime, timezone
        record = dict(result)
        record["files"] = [si_name, bl_name]
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        try:
            ref = db.collection("shipwise_results").document()
            ref.set(record)
            firestore_id = ref.id
        except Exception:
            pass

    return {
        "result": result,
        "files": [si_name, bl_name],
        "firestore_id": firestore_id,
    }
