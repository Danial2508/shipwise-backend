from pathlib import Path
import sys

BUNDLE_PATH = Path(r"C:\for\sdoc-hackathon-bundle")
sys.path.insert(0, str(BUNDLE_PATH))

from loader import Inbox


inbox = Inbox(str(BUNDLE_PATH))

for email_id in [
    "email_512",
    "email_513",
    "email_514"
]:

    email = inbox.get(email_id)

    print("\n" + "=" * 60)
    print(email_id)
    print("=" * 60)

    for attachment in email.get("attachments", []):

        if attachment.lower().endswith(".pdf"):

            print("\nAttachment:")
            print(attachment)

            data = inbox.read_bytes(attachment)

            print("File size:", len(data), "bytes")

            print("First 20 bytes:")
            print(data[:20])