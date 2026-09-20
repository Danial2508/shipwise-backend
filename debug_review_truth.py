import json
from pathlib import Path

SUBMISSION = Path(r"C:\SHIPWISE-AI\backend\submission.json")
GROUND_TRUTH = Path(r"C:\for\sdoc-hackathon-docker\data_v2\ground_truth.json")

with open(SUBMISSION, "r", encoding="utf-8") as f:
    submission = json.load(f)

with open(GROUND_TRUTH, "r", encoding="utf-8") as f:
    truth = json.load(f)

print("=" * 70)
print("PREDICTED NEEDS_REVIEW vs GROUND TRUTH")
print("=" * 70)

total = 0
correct_review = 0
false_review = 0

for email_id, pred in submission.items():

    if pred.get("status") == "NEEDS_REVIEW":

        total += 1
        actual = truth[email_id]

        print()
        print(email_id)
        print("PRED :", pred.get("status"), pred.get("review_reason"))
        print("TRUE :", actual.get("status"), actual.get("review_reason"))

        if actual.get("status") == "NEEDS_REVIEW":
            correct_review += 1
        else:
            false_review += 1

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("Predicted review :", total)
print("Correct review   :", correct_review)
print("False review     :", false_review)