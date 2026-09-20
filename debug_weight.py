import sys
from pathlib import Path

sys.path.insert(0, r"C:\for\sdoc-hackathon-bundle")

from document_reader import read_document
from loader import Inbox

BUNDLE = r"C:\for\sdoc-hackathon-bundle"
inbox = Inbox(BUNDLE)

for x in ["351", "499"]:
    email = inbox.get(f"email_{x}")

    print("\n" + "=" * 70)
    print(f"EMAIL {x}")

    for attachment in email.get("attachments", []):
        name = Path(attachment).name

        if f"email_{x}_SI." in name or f"email_{x}_BL." in name:
            print("\n---", name, "---")

            text = read_document(inbox, attachment)

            # Print lines containing weight-related terms
            for i, line in enumerate(text.splitlines()):
                if any(word in line.lower() for word in [
                    "weight",
                    "gross",
                    "kgs",
                    "kg"
                ]):
                    print(f"{i}: {repr(line)}")