import sys
import json
from collections import Counter

sys.path.insert(0, r"C:\for\sdoc-hackathon-bundle")

from loader import Inbox
from extractor import extract_fields


inbox = Inbox(r"C:\for\sdoc-hackathon-bundle")

with open("submission.json", "r", encoding="utf-8") as file:
    submission = json.load(file)


review_ids = [
    email_id
    for email_id, result in submission.items()
    if result["status"] == "NEEDS_REVIEW"
]

print("Review emails:", len(review_ids))

missing_fields = Counter()

for email_id in review_ids:

    email = inbox.get(email_id)

    for attachment in email["attachments"]:

        try:
            text = inbox.read_text(attachment)
            fields = extract_fields(text)

            for field, value in fields.items():
                if value is None:
                    missing_fields[field] += 1

        except Exception:
            pass


print("\n=== MISSING FIELD COUNT ===")

for field, count in missing_fields.most_common():
    print(f"{field}: {count}")