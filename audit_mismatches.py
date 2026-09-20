import sys
from pathlib import Path

BUNDLE_PATH = Path(
    r"C:\for\sdoc-hackathon-bundle"
)

PROJECT_DIR = Path(
    __file__
).resolve().parent

sys.path.insert(
    0,
    str(BUNDLE_PATH)
)

from loader import Inbox

from classifier import classify_email

from document_reader import read_document

from extractor import extract_fields

from comparator import compare_documents


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


def main():

    inbox = Inbox(
        str(BUNDLE_PATH)
    )

    emails = list(
        inbox.emails()
    )

    mismatch_count = 0

    for email in emails:

        if classify_email(email) != "BL_COMPARISON":
            continue

        attachments = email.get(
            "attachments",
            []
        )

        si_attachment = find_si_attachment(
            attachments
        )

        bl_attachment = find_bl_attachment(
            attachments
        )

        if not si_attachment or not bl_attachment:
            continue

        try:

            si_text = read_document(
                inbox,
                si_attachment
            )

            bl_text = read_document(
                inbox,
                bl_attachment
            )

            si_fields = extract_fields(
                si_text
            )

            bl_fields = extract_fields(
                bl_text
            )

        except Exception:

            continue

        # Skip incomplete cases
        if any(
            value is None
            for value in si_fields.values()
        ):

            continue

        if any(
            value is None
            for value in bl_fields.values()
        ):

            continue

        result = compare_documents(
            si_fields,
            bl_fields
        )

        if result["status"] != "MISMATCH":
            continue

        mismatch_count += 1

        print("\n" + "=" * 70)

        print(
            f"MISMATCH #{mismatch_count}"
        )

        print(
            f"EMAIL: {email['email_id']}"
        )

        print(
            f"SI: {si_attachment}"
        )

        print(
            f"BL: {bl_attachment}"
        )

        print("-" * 70)

        for field in result[
            "defect_fields"
        ]:

            difference = result[
                "differences"
            ][field]

            print(
                f"\nFIELD: {field}"
            )

            print(
                f"  SI: {difference['si_value']}"
            )

            print(
                f"  BL: {difference['bl_value']}"
            )

            print(
                f"  REASON: {difference['reason']}"
            )

    print("\n" + "=" * 70)

    print(
        f"TOTAL MISMATCHES: {mismatch_count}"
    )


if __name__ == "__main__":

    main()