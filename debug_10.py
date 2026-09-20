import sys
from pathlib import Path

sys.path.insert(0, r"C:\for\sdoc-hackathon-bundle")

from extractor import extract_fields
from document_reader import read_document
from loader import Inbox


BUNDLE = r"C:\for\sdoc-hackathon-bundle"

inbox = Inbox(BUNDLE)

ids = [
    "097", "107", "291", "302", "313",
    "351", "354", "434", "435", "499"
]

for x in ids:

    print("\n" + "=" * 60)
    print("EMAIL", x)

    email = inbox.get(f"email_{x}")

    attachments = email.get("attachments", [])

    for attachment in attachments:

        name = Path(attachment).name

        if f"email_{x}_SI." in name or f"email_{x}_BL." in name:

            try:
                text = read_document(inbox, attachment)
                fields = extract_fields(text)

                print(f"\n--- {name} ---")
                print(fields)

            except Exception as e:
                print(f"\n--- {name}: ERROR ---")
                print(e)