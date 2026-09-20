import json
import sys
from pathlib import Path

# =========================================================
# PATHS
# =========================================================

BUNDLE_PATH = Path(r"C:\for\sdoc-hackathon-bundle")
DOCKER_PATH = Path(r"C:\for\sdoc-hackathon-docker")

SUBMISSION_PATH = Path(
    r"C:\SHIPWISE-AI\backend\submission.json"
)

GROUND_TRUTH_PATH = (
    DOCKER_PATH
    / "data_v2"
    / "ground_truth.json"
)

sys.path.insert(
    0,
    str(BUNDLE_PATH)
)

from loader import Inbox


# =========================================================
# LOAD DATA
# =========================================================

inbox = Inbox(
    str(BUNDLE_PATH)
)

with open(
    SUBMISSION_PATH,
    "r",
    encoding="utf-8"
) as file:

    submission = json.load(file)


with open(
    GROUND_TRUTH_PATH,
    "r",
    encoding="utf-8"
) as file:

    ground_truth = json.load(file)


# =========================================================
# FIND FALSE-NEGATIVE BL_COMPARISON
# =========================================================

cases = []

for email_id, truth in ground_truth.items():

    actual = truth.get("category")
    predicted = submission.get(
        email_id,
        {}
    ).get("category")

    if (
        actual == "BL_COMPARISON"
        and predicted != "BL_COMPARISON"
    ):

        cases.append(
            email_id
        )


# =========================================================
# PRINT SUMMARY
# =========================================================

print("=" * 80)
print("BL_COMPARISON FALSE-NEGATIVE AUDIT")
print("=" * 80)

print(
    f"\nTotal false negatives: {len(cases)}"
)


# =========================================================
# PRINT EMAIL DETAILS
# =========================================================

for number, email_id in enumerate(
    cases,
    start=1
):

    email = inbox.get(
        email_id
    )

    predicted = submission[
        email_id
    ].get("category")

    truth = ground_truth[
        email_id
    ].get("category")

    print("\n" + "=" * 80)

    print(
        f"[{number}/{len(cases)}] {email_id}"
    )

    print(
        f"GROUND TRUTH : {truth}"
    )

    print(
        f"OUR CATEGORY : {predicted}"
    )

    print(
        "\nSUBJECT:"
    )

    print(
        email.get(
            "subject",
            ""
        )
    )

    print(
        "\nBODY:"
    )

    print(
        email.get(
            "body",
            ""
        )[:1000]
    )

    print(
        "\nATTACHMENTS:"
    )

    for attachment in email.get(
        "attachments",
        []
    ):

        print(
            f"  - {attachment}"
        )


print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)