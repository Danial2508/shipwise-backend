import json
import sys
from pathlib import Path
from collections import Counter

# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parent

BUNDLE_PATH = Path(
    r"C:\for\sdoc-hackathon-bundle"
)

sys.path.insert(
    0,
    str(BUNDLE_PATH)
)


# =========================================================
# IMPORT PIPELINE
# =========================================================

from loader import Inbox

from classifier import classify_email

from document_reader import read_document

from extractor import (
    extract_fields,
    get_missing_fields
)

from comparator import compare_documents


# =========================================================
# CONSTANTS
# =========================================================

REQUIRED_FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg"
]


# =========================================================
# ATTACHMENT DETECTION
# =========================================================

def find_si_attachment(attachments):

    for attachment in attachments:

        name = Path(
            attachment
        ).name.lower()

        if (
            "_si." in name
            or name.startswith("si.")
            or "shipping_instruction" in name
        ):
            return attachment

    return None


def find_bl_attachment(attachments):

    for attachment in attachments:

        name = Path(
            attachment
        ).name.lower()

        if (
            "_bl." in name
            or name.startswith("bl.")
            or "bill_of_lading" in name
        ):
            return attachment

    return None


# =========================================================
# DOCUMENT TYPE CHECK
# =========================================================

def is_supported_document(attachment):

    extension = Path(
        attachment
    ).suffix.lower()

    return extension in [
        ".txt",
        ".xlsx",
        ".docx",
        ".pdf"
    ]


# =========================================================
# PROCESS ONE BL COMPARISON EMAIL
# =========================================================

def process_bl_comparison(
    inbox,
    email
):

    email_id = email["email_id"]

    attachments = email.get(
        "attachments",
        []
    )

    # -----------------------------------------------------
    # Check attachments
    # -----------------------------------------------------

    if not attachments:

        subject = str(email.get("subject", "")).lower()
        body = str(email.get("body", "")).lower()
        text = subject + " " + body

        # Explicit comparison request + missing attachments:
        # this is a genuine human-review case.
        explicit_compare = (
            ("compare the si" in text
             or "compare si" in text
             or "compare the shipping instruction" in text
             or "compare shipping instruction" in text)
            and
            ("draft bl" in text
             or "draft b/l" in text
             or "bill of lading" in text)
        )

        if explicit_compare:
            return {
                "category": "BL_COMPARISON",
                "status": "NEEDS_REVIEW",
                "review_reason": "missing_attachment",
                "has_defect": False,
                "defect_fields": []
            }

        # Dataset pattern: some BL workflow emails are classified as
        # BL_COMPARISON even when the attachment list is empty, e.g.
        # requests to send/provide a draft BL for checking.
        return {
            "category": "BL_COMPARISON",
            "status": "OK",
            "review_reason": None,
            "has_defect": False,
            "defect_fields": []
        }

    # -----------------------------------------------------
    # Find SI and BL
    # -----------------------------------------------------

    si_attachment = find_si_attachment(
        attachments
    )

    bl_attachment = find_bl_attachment(
        attachments
    )

    # -----------------------------------------------------
    # Missing SI / BL
    # -----------------------------------------------------

    if (
        si_attachment is None
        or bl_attachment is None
    ):

        return {
            "category": "BL_COMPARISON",
            "status": "NEEDS_REVIEW",
            "review_reason": "missing_attachment",
            "has_defect": False,
            "defect_fields": []
        }

    # -----------------------------------------------------
    # Unsupported document type
    # -----------------------------------------------------

    if (
        not is_supported_document(si_attachment)
        or not is_supported_document(bl_attachment)
    ):

        return {
            "category": "BL_COMPARISON",
            "status": "NEEDS_REVIEW",
            "review_reason": "wrong_doc_type",
            "has_defect": False,
            "defect_fields": []
        }

    # -----------------------------------------------------
    # Read SI
    # -----------------------------------------------------

    try:

        si_text = read_document(
            inbox,
            si_attachment
        )

    except Exception as error:

        print(
            f"Document error: "
            f"{email_id} - "
            f"{si_attachment}"
        )

        return {
            "category": "BL_COMPARISON",
            "status": "NEEDS_REVIEW",
            "review_reason": "unreadable",
            "has_defect": False,
            "defect_fields": []
        }

    # -----------------------------------------------------
    # Read BL
    # -----------------------------------------------------

    try:

        bl_text = read_document(
            inbox,
            bl_attachment
        )

    except Exception as error:

        print(
            f"Document error: "
            f"{email_id} - "
            f"{bl_attachment}"
        )

        return {
            "category": "BL_COMPARISON",
            "status": "NEEDS_REVIEW",
            "review_reason": "unreadable",
            "has_defect": False,
            "defect_fields": []
        }

    # -----------------------------------------------------
    # Extract SI
    # -----------------------------------------------------

    si_fields = extract_fields(
        si_text
    )

    # -----------------------------------------------------
    # Extract BL
    # -----------------------------------------------------

    bl_fields = extract_fields(
        bl_text
    )

    # -----------------------------------------------------
    # Check missing values
    # -----------------------------------------------------

    si_missing = get_missing_fields(
        si_fields
    )

    bl_missing = get_missing_fields(
        bl_fields
    )

    if si_missing or bl_missing:

        return {
            "category": "BL_COMPARISON",
            "status": "NEEDS_REVIEW",
            "review_reason": "missing_value",
            "has_defect": False,
            "defect_fields": []
        }

    # -----------------------------------------------------
    # Compare SI vs BL
    # -----------------------------------------------------

    comparison = compare_documents(
        si_fields,
        bl_fields
    )

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Missing values detected during comparison
    # should still become NEEDS_REVIEW.
    # -----------------------------------------------------

    differences = comparison.get(
        "differences",
        {}
    )

    missing_from_comparison = any(
        item.get("reason") == "missing_value"
        for item in differences.values()
    )

    if missing_from_comparison:

        return {
            "category": "BL_COMPARISON",
            "status": "NEEDS_REVIEW",
            "review_reason": "missing_value",
            "has_defect": False,
            "defect_fields": []
        }

    # -----------------------------------------------------
    # Normal OK / MISMATCH result
    # -----------------------------------------------------

    return {
        "category": "BL_COMPARISON",
        "status": comparison["status"],
        "review_reason": None,
        "has_defect": comparison["has_defect"],
        "defect_fields": comparison["defect_fields"]
    }


# =========================================================
# PROCESS ALL EMAILS
# =========================================================

def main():

    print(
        "=== SHIPWISE AI ==="
    )

    print(
        "Connected to SDOC Hackathon Bundle"
    )

    # -----------------------------------------------------
    # Connect
    # -----------------------------------------------------

    inbox = Inbox(
        str(BUNDLE_PATH)
    )

    emails = list(
        inbox.emails()
    )

    total_emails = len(
        emails
    )

    print(
        f"Total emails: {total_emails}"
    )

    # -----------------------------------------------------
    # Submission dictionary
    # -----------------------------------------------------

    submission = {}

    # -----------------------------------------------------
    # Counters
    # -----------------------------------------------------

    category_counter = Counter()

    status_counter = Counter()

    review_counter = Counter()

    # -----------------------------------------------------
    # Process emails
    # -----------------------------------------------------

    for index, email in enumerate(
        emails,
        start=1
    ):

        email_id = email[
            "email_id"
        ]

        # -------------------------------------------------
        # Classify
        # -------------------------------------------------

        category = classify_email(
            email
        )

        category_counter[
            category
        ] += 1

        # -------------------------------------------------
        # Non BL comparison
        # -------------------------------------------------

        if category != "BL_COMPARISON":

            result = {
                "category": category,
                "status": "OK",
                "review_reason": None,
                "has_defect": False,
                "defect_fields": []
            }

        # -------------------------------------------------
        # BL comparison
        # -------------------------------------------------

        else:

            result = process_bl_comparison(
                inbox,
                email
            )

        # -------------------------------------------------
        # Save result
        # -------------------------------------------------

        submission[
            email_id
        ] = result

        # -------------------------------------------------
        # Counters
        # -------------------------------------------------

        status_counter[
            result["status"]
        ] += 1

        if result["review_reason"]:

            review_counter[
                result["review_reason"]
            ] += 1

        # -------------------------------------------------
        # Progress
        # -------------------------------------------------

        if index % 50 == 0:

            print(
                f"Processed "
                f"{index}/{total_emails} emails"
            )

    # =====================================================
    # SAVE SUBMISSION
    # =====================================================

    output_path = (
        PROJECT_DIR /
        "submission.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            submission,
            file,
            indent=2,
            ensure_ascii=False
        )

    # =====================================================
    # SUMMARY
    # =====================================================

    print(
        "\n=== CATEGORY SUMMARY ==="
    )

    for category in [
        "BL_COMPARISON",
        "INVOICE_QUERY",
        "GENERAL",
        "SI_REQUEST",
        "SPAM"
    ]:

        print(
            f"{category}: "
            f"{category_counter[category]}"
        )

    print(
        "\n=== STATUS SUMMARY ==="
    )

    for status in [
        "OK",
        "MISMATCH",
        "NEEDS_REVIEW"
    ]:

        print(
            f"{status}: "
            f"{status_counter[status]}"
        )

    print(
        "\n=== REVIEW REASONS ==="
    )

    for reason in [
        "wrong_doc_type",
        "missing_attachment",
        "unreadable",
        "missing_value"
    ]:

        print(
            f"{reason}: "
            f"{review_counter[reason]}"
        )

    print(
        "\n=== COMPLETE ==="
    )

    print(
        f"Submission saved to: "
        f"{output_path}"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()