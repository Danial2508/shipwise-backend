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


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# FIREBASE / FIRESTORE
# =========================================================

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


# =========================================================
# BASIC ENDPOINTS
# =========================================================

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
        return {
            "firestore": False,
            "error": FIREBASE_ERROR,
        }

    try:
        list(
            db.collection("shipwise_results")
            .limit(1)
            .stream()
        )

        return {
            "firestore": True
        }

    except Exception as exc:
        return {
            "firestore": False,
            "error": str(exc),
        }


@app.get("/results")
def get_results():
    db = get_db()

    if db is None:
        return {
            "results": [],
            "firestore": False,
        }

    docs = db.collection("shipwise_results").stream()

    results = []

    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        results.append(item)

    return {
        "results": results,
        "firestore": True,
    }


@app.post("/results")
def save_result(payload: dict):
    db = get_db()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Firestore unavailable"
        )

    from datetime import datetime, timezone

    payload = dict(payload)

    payload["created_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    ref = db.collection(
        "shipwise_results"
    ).document()

    ref.set(payload)

    return {
        "saved": True,
        "id": ref.id,
        "result": payload,
    }


# =========================================================
# UPLOAD ADAPTER
# =========================================================

class UploadedInbox:

    def __init__(self, files):
        self.files = files

    def read_bytes(self, attachment):
        return self.files[attachment]

    def read_text(
        self,
        attachment,
        encoding="utf-8"
    ):
        return self.files[attachment].decode(
            encoding,
            errors="replace"
        )


# =========================================================
# DOCUMENT CONFIG
# =========================================================

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".xlsx",
    ".docx",
    ".pdf",
}


def role(filename):

    name = Path(filename).name.lower()

    if (
        "_si." in name
        or name.startswith("si.")
        or "shipping_instruction" in name
    ):
        return "si"

    if (
        "_bl." in name
        or name.startswith("bl.")
        or "bill_of_lading" in name
    ):
        return "bl"

    return None


# =========================================================
# REVIEW RESULT
# =========================================================

def review_result(reason):

    return {
        "category": "BL_COMPARISON",
        "status": "NEEDS_REVIEW",
        "review_reason": reason,
        "has_defect": False,
        "defect_fields": [],
    }


# =========================================================
# FRONTEND FIELD FORMATTER
# =========================================================

def frontend_fields(fields):

    return {
        "shipper": fields.get("shipper"),
        "consignee": fields.get("consignee"),
        "notify_party": fields.get("notify_party"),
        "pol": fields.get("port_of_loading"),
        "pod": fields.get("port_of_discharge"),
        "container_count": fields.get("container_count"),
        "gross_weight": fields.get("gross_weight_kg"),
    }


# =========================================================
# REAL DOCUMENT PROCESSOR
# =========================================================

@app.post("/process")
async def process_documents(
    files: List[UploadFile] = File(...)
):

    # -----------------------------------------------------
    # CHECK FILES
    # -----------------------------------------------------

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files uploaded"
        )


    # -----------------------------------------------------
    # READ UPLOADED FILES
    # -----------------------------------------------------

    stored = {}

    for upload in files:

        filename = Path(
            upload.filename or ""
        ).name

        suffix = Path(
            filename
        ).suffix.lower()

        if not filename:
            continue

        if suffix not in SUPPORTED_EXTENSIONS:

            return {
                "result": review_result(
                    "wrong_doc_type"
                ),
                "documents": [],
                "message": (
                    f"Unsupported document type: "
                    f"{suffix or 'unknown'}"
                ),
            }

        data = await upload.read()

        if not data:

            return {
                "result": review_result(
                    "unreadable"
                ),
                "documents": [
                    {
                        "filename": filename
                    }
                ],
                "message": (
                    f"Empty file: {filename}"
                ),
            }

        stored[filename] = data


    # -----------------------------------------------------
    # IDENTIFY SI + BL
    # -----------------------------------------------------

    si_name = next(
        (
            name
            for name in stored
            if role(name) == "si"
        ),
        None
    )

    bl_name = next(
        (
            name
            for name in stored
            if role(name) == "bl"
        ),
        None
    )


    # -----------------------------------------------------
    # MISSING DOCUMENT
    # -----------------------------------------------------

    if si_name is None or bl_name is None:

        return {
            "result": review_result(
                "missing_attachment"
            ),
            "documents": [
                {
                    "filename": name
                }
                for name in stored
            ],
            "message": (
                "Upload one SI and one BL document. "
                "Filenames should contain _SI and _BL."
            ),
        }


    # -----------------------------------------------------
    # CREATE UPLOAD INBOX
    # -----------------------------------------------------

    inbox = UploadedInbox(stored)


    # -----------------------------------------------------
    # READ DOCUMENTS
    # -----------------------------------------------------

    try:

        si_text = read_document(
            inbox,
            si_name
        )

        bl_text = read_document(
            inbox,
            bl_name
        )

    except Exception as exc:

        result = review_result(
            "unreadable"
        )

        result["message"] = str(exc)

        return {
            "result": result,
            "documents": [
                {
                    "filename": si_name
                },
                {
                    "filename": bl_name
                },
            ],
        }


    # -----------------------------------------------------
    # EXTRACT FIELDS
    # -----------------------------------------------------

    si_fields = extract_fields(
        si_text
    )

    bl_fields = extract_fields(
        bl_text
    )


    # -----------------------------------------------------
    # CHECK MISSING FIELDS
    # -----------------------------------------------------

    si_missing = get_missing_fields(
        si_fields
    )

    bl_missing = get_missing_fields(
        bl_fields
    )


    # -----------------------------------------------------
    # COMPARISON
    # -----------------------------------------------------

    if si_missing or bl_missing:

        result = review_result(
            "missing_value"
        )

        result.update(
            {
                "si_fields": si_fields,
                "bl_fields": bl_fields,
                "missing_si_fields": si_missing,
                "missing_bl_fields": bl_missing,
            }
        )

    else:

        comparison = compare_documents(
            si_fields,
            bl_fields
        )

        differences = comparison.get(
            "differences",
            {}
        )


        # -------------------------------------------------
        # MISSING VALUE DURING COMPARISON
        # -------------------------------------------------

        if any(
            item.get("reason") == "missing_value"
            for item in differences.values()
        ):

            result = review_result(
                "missing_value"
            )

            result.update(
                {
                    "si_fields": si_fields,
                    "bl_fields": bl_fields,
                    "differences": differences,
                }
            )


        # -------------------------------------------------
        # NORMAL COMPARISON RESULT
        # -------------------------------------------------

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


    # =====================================================
    # SAVE TO FIRESTORE
    # =====================================================

    db = get_db()

    firestore_id = None

    if db is not None:

        from datetime import datetime, timezone

        record = dict(result)

        record["files"] = [
            si_name,
            bl_name,
        ]

        record["created_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        try:

            ref = (
                db.collection(
                    "shipwise_results"
                )
                .document()
            )

            ref.set(record)

            firestore_id = ref.id

        except Exception:

            pass


    # =====================================================
    # FRONTEND COMPATIBILITY
    # =====================================================

    documents = [
        {
            "filename": si_name
        },
        {
            "filename": bl_name
        },
    ]


    # Frontend expects "mismatches"
    result["mismatches"] = result.get(
        "defect_fields",
        []
    )


    # Frontend expects SI/BL structure
    if (
        "si_fields" in result
        and "bl_fields" in result
    ):

        result["si"] = {
            "fields": frontend_fields(
                result["si_fields"]
            )
        }

        result["bl"] = {
            "fields": frontend_fields(
                result["bl_fields"]
            )
        }


    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {
        "result": result,

        "documents": documents,

        "files": [
            si_name,
            bl_name
        ],

        "firestore_id": firestore_id,
    }