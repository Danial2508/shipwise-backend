from pathlib import Path
import sys

BUNDLE_PATH = Path(r"C:\for\sdoc-hackathon-bundle")
sys.path.insert(0, str(BUNDLE_PATH))

from loader import Inbox
from document_reader import read_document


inbox = Inbox(str(BUNDLE_PATH))


for email_id in [
    "email_512",
    "email_513",
    "email_514"
]:

    email = inbox.get(email_id)

    print("\n" + "=" * 70)
    print(email_id)
    print("=" * 70)

    for attachment in email.get("attachments", []):

        if not attachment.lower().endswith(".pdf"):
            continue

        print("\nATTACHMENT:")
        print(attachment)

        try:

            text = read_document(
                inbox,
                attachment
            )

            print("\n--- OCR / EXTRACTED TEXT ---")
            print(text[:3000])

        except Exception as error:

            print(
                "\nERROR:",
                error
            )