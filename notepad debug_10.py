from extractor import extract_fields
from document_reader import read_document
from pathlib import Path

base = Path(r"C:\for\sdoc-hackathon-bundle\attachments")

ids = [
    "097", "107", "291", "302", "313",
    "351", "354", "434", "435", "499"
]

for x in ids:

    print("\n" + "=" * 60)
    print("EMAIL", x)

    for doc_type in ["SI", "BL"]:

        files = list(base.glob(f"email_{x}_{doc_type}.*"))

        if not files:
            print(doc_type, "NOT FOUND")
            continue

        path = files[0]

        try:
            text = read_document(str(path), path.name)
            fields = extract_fields(text)

            print(f"\n--- {doc_type}: {path.name} ---")
            print(fields)

        except Exception as e:
            print(f"\n--- {doc_type}: ERROR ---")
            print(e)