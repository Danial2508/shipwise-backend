import json
from pathlib import Path

SUBMISSION = Path("submission.json")

with open(
    SUBMISSION,
    "r",
    encoding="utf-8"
) as file:
    submission = json.load(file)


print("=" * 70)
print("NEEDS_REVIEW AUDIT")
print("=" * 70)

for email_id, result in submission.items():

    if result["status"] != "NEEDS_REVIEW":
        continue

    print("\n" + "-" * 70)

    print("EMAIL:", email_id)

    print(
        "CATEGORY:",
        result["category"]
    )

    print(
        "REASON:",
        result["review_reason"]
    )

    print(
        "DEFECT FIELDS:",
        result["defect_fields"]
    )