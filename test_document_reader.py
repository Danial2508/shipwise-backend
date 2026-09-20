import sys

sys.path.insert(0, r"C:\for\sdoc-hackathon-bundle")

from loader import Inbox
from document_reader import read_document


inbox = Inbox(r"C:\for\sdoc-hackathon-bundle")

email = inbox.get("email_001")

for attachment in email["attachments"]:

    print("\n================================")
    print("FILE:", attachment)
    print("================================")

    try:
        text = read_document(inbox, attachment)
        print(text[:3000])

    except Exception as error:
        print("ERROR:", error)