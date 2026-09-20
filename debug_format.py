import sys

sys.path.insert(0, r"C:\for\sdoc-hackathon-bundle")

from loader import Inbox
from extractor import extract_fields


inbox = Inbox(r"C:\for\sdoc-hackathon-bundle")

for email in inbox:

    if not email["attachments"]:
        continue

    for attachment in email["attachments"]:

        try:
            text = inbox.read_text(attachment)
            fields = extract_fields(text)

            if (
                fields["port_of_loading"] is None
                and fields["port_of_discharge"] is None
                and fields["container_count"] is None
            ):
                print("EMAIL:", email["email_id"])
                print("ATTACHMENT:", attachment)
                print("\n=== DOCUMENT ===")
                print(text)
                print("=== END ===")
                raise SystemExit

        except Exception:
            continue