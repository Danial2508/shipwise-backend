import re


CATEGORIES = [
    "BL_COMPARISON",
    "SI_REQUEST",
    "INVOICE_QUERY",
    "GENERAL",
    "SPAM"
]


def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def classify_email(email):

    subject = normalize_text(
        email.get("subject", "")
    )

    body = normalize_text(
        email.get("body", "")
    )

    text = subject + " " + body

    attachments = email.get(
        "attachments",
        []
    )

    attachment_text = " ".join(
        str(a).lower()
        for a in attachments
    )


    # =====================================================
    # KEYWORDS
    # =====================================================

    has_bl_keyword = (
        "bl" in text
        or "bill of lading" in text
        or "draft b/l" in text
        or "draft bl" in text
    )

    has_si_keyword = (
        "si" in text
        or "shipping instruction" in text
        or "shipping instructions" in text
    )


    # =====================================================
    # ATTACHMENT DETECTION
    # =====================================================

    has_bl_attachment = any(
        "_bl." in a
        or "bl." in a
        or "bill_of_lading" in a
        for a in attachment_text.split()
    )

    has_si_attachment = any(
        "_si." in a
        or "si." in a
        or "shipping_instruction" in a
        for a in attachment_text.split()
    )


    # =====================================================
    # STRONG BL COMPARISON REQUESTS
    # =====================================================

    explicit_compare = (
        (
            "compare the si" in text
            or "compare si" in text
            or "compare the shipping instruction" in text
            or "compare shipping instruction" in text
        )
        and (
            "draft bl" in text
            or "draft b/l" in text
            or "bill of lading" in text
        )
    )


    # =====================================================
    # DRAFT BL CHECKING REQUEST
    # =====================================================

    draft_bl_check = (
        (
            "draft bl" in text
            or "draft b/l" in text
            or "bill of lading" in text
        )
        and (
            "for checking" in text
            or "for check" in text
            or "to confirm docs" in text
            or "confirm docs" in text
            or "request bl draft" in text
            or "request draft bl" in text
            or "amend bl" in text
        )
    )


    # =====================================================
    # ATTACHMENT PAIR
    # =====================================================

    attachment_pair = (
        has_bl_attachment
        and has_si_attachment
    )


    # =====================================================
    # BL COMPARISON
    # =====================================================

    # Explicit comparison request
    if explicit_compare:
        return "BL_COMPARISON"


    # Draft BL checking workflow
    if draft_bl_check:
        return "BL_COMPARISON"


    # SI + BL attachments
    if attachment_pair:
        return "BL_COMPARISON"


    # =====================================================
    # SI REQUEST
    # =====================================================

    if (
        "shipping instruction" in text
        or "shipping instructions" in text
        or "request si" in text
        or "new si" in text
    ):
        return "SI_REQUEST"


    # =====================================================
    # INVOICE
    # =====================================================

    if (
        "invoice" in text
        or "billing" in text
        or "payment" in text
    ):
        return "INVOICE_QUERY"


    # =====================================================
    # SPAM
    # =====================================================

    spam_words = [
        "winner",
        "lottery",
        "prize",
        "promotion",
        "click here"
    ]

    if any(
        word in text
        for word in spam_words
    ):
        return "SPAM"


    # =====================================================
    # GENERAL
    # =====================================================

    return "GENERAL"