from pathlib import Path
import sys

BUNDLE_PATH = Path(r"C:\for\sdoc-hackathon-bundle")
sys.path.insert(0, str(BUNDLE_PATH))

from loader import Inbox
import fitz


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

        if not attachment.lower().endswith(".pdf"):
            continue

        data = inbox.read_bytes(attachment)

        print("\nAttachment:", attachment)
        print("Size:", len(data), "bytes")

        try:
            pdf = fitz.open(
                stream=data,
                filetype="pdf"
            )

            print("Pages:", len(pdf))

            for page_number, page in enumerate(pdf):

                text = page.get_text("text").strip()
                images = page.get_images(full=True)

                print(
                    f"Page {page_number + 1}: "
                    f"text_chars={len(text)}, "
                    f"images={len(images)}"
                )

            pdf.close()

        except Exception as error:

            print("ERROR:", error)