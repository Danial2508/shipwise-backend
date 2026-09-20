import sys
import json
from pathlib import Path
from collections import Counter

sys.path.insert(
    0,
    r"C:\for\sdoc-hackathon-bundle"
)

from loader import Inbox
from document_reader import read_document
from extractor import extract_fields


BUNDLE_PATH = r"C:\for\sdoc-hackathon-bundle"


FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg"
]


inbox = Inbox(BUNDLE_PATH)

with open(
    "submission.json",
    "r",
    encoding="utf-8"
) as file:

    submission = json.load(file)


review_ids = [
    email_id
    for email_id, result in submission.items()
    if (
        result["status"] == "NEEDS_REVIEW"
        and result["review_reason"] == "missing_value"
    )
]


field_counter = Counter()
format_counter = Counter()


print(
    f"Missing-value cases: {len(review_ids)}"
)

print(
    "\n======================================"
)

for email_id in review_ids:

    email = inbox.get(email_id)

    print(
        f"\n### {email_id}"
    )

    for attachment in email.get(
        "attachments",
        []
    ):

        name = Path(
            attachment
        ).name

        extension = Path(
            attachment
        ).suffix.lower()

        try:

            text = read_document(
                inbox,
                attachment
            )

            fields = extract_fields(
                text
            )

            missing = [
                field
                for field in FIELDS
                if fields.get(field) is None
            ]

            if missing:

                format_counter[
                    extension
                ] += 1

                for field in missing:

                    field_counter[
                        field
                    ] += 1

                print(
                    f"{name}"
                )

                print(
                    f"  Missing: {missing}"
                )

                # Show document lines containing likely labels
                lines = text.splitlines()

                useful_lines = []

                keywords = [
                    "ship",
                    "consignee",
                    "notify",
                    "port",
                    "load",
                    "discharge",
                    "container",
                    "gross",
                    "weight"
                ]

                for line in lines:

                    line_lower = line.lower()

                    if any(
                        keyword in line_lower
                        for keyword in keywords
                    ):

                        useful_lines.append(
                            line.strip()
                        )

                for line in useful_lines[:15]:

                    print(
                        f"  {line}"
                    )

        except Exception as error:

            print(
                f"{name} ERROR: {error}"
            )


print(
    "\n======================================"
)

print(
    "\n=== MISSING FIELD SUMMARY ==="
)

for field, count in field_counter.most_common():

    print(
        f"{field}: {count}"
    )


print(
    "\n=== FILE FORMAT SUMMARY ==="
)

for extension, count in format_counter.most_common():

    print(
        f"{extension}: {count}"
    )