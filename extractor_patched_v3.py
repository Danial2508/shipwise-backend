import re


REQUIRED_FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg"
]


# =========================================================
# CLEAN VALUE
# =========================================================

def clean_value(value):
    if value is None:
        return None

    value = str(value)
    value = value.replace("\r", " ").replace("\n", " ")
    value = re.sub(r"\s+", " ", value).strip()

    if "|" in value:
        value = value.split("|")[0].strip()

    if not value:
        return None

    # Obvious placeholders = missing
    if value.upper() in [
        "N/A",
        "NA",
        "TBA",
        "TBD",
        "NIL",
        "NONE",
        "____",
        "_____",
        "______",
        "???"
    ]:
        return None

    return value


# =========================================================
# LABEL NORMALIZATION
# =========================================================

def simplify_label(label):
    if label is None:
        return ""

    label = str(label).lower()

    # Remove bilingual text inside parentheses
    label = re.sub(r"\([^)]*\)", " ", label)

    # Remove Chinese characters
    label = re.sub(r"[\u4e00-\u9fff]+", " ", label)

    # Normalize separators
    label = label.replace(":", " ")
    label = label.replace("/", " ")
    label = label.replace("-", " ")

    label = re.sub(r"\s+", " ", label)

    return label.strip()


# =========================================================
# LABEL DEFINITIONS
# =========================================================

SHIPPER_LABELS = [
    "shipper/exporter",
    "shipper (principal or seller)",
    "shipper exporter",
    "shipper",
    "exporter"
]


CONSIGNEE_LABELS = [
    "consignee (non-negotiable)",
    "to the order of",
    "consignee"
]


# IMPORTANT:
# Longer / more specific labels will be checked first.
NOTIFY_LABELS = [
    "notify party/intermediate consignee",
    "party/intermediate consignee",
    "notify party",
    "notify"
]


POL_LABELS = [
    "port of loading (pol)",
    "port of loading",
    "load port",
    "pol"
]


POD_LABELS = [
    "port of discharge (pod)",
    "port of discharge",
    "discharge port",
    "pod"
]


CONTAINER_LABELS = [
    "no. of containers or packages",
    "no. of containers",
    "total containers",
    "container count",
    "no of containers",
    "total container"
]


WEIGHT_LABELS = [
    "gross wt (kgs) (æ¯›é‡ kgs)",
    "gross weightæ¯›é‡(kgs)",
    "gross weight (kg)",
    "gross wt (kgs)",
    "total gross weight",
    "gross weight",
    "gross wt"
]


# =========================================================
# LABEL MATCHING
# =========================================================

def label_matches(label, candidates):
    simplified = simplify_label(label)

    for candidate in candidates:
        candidate_simplified = simplify_label(candidate)

        if simplified == candidate_simplified:
            return True

    return False


def is_any_known_label(label):
    all_labels = (
        SHIPPER_LABELS
        + CONSIGNEE_LABELS
        + NOTIFY_LABELS
        + POL_LABELS
        + POD_LABELS
        + CONTAINER_LABELS
        + WEIGHT_LABELS
    )

    return any(
        label_matches(label, [candidate])
        for candidate in all_labels
    )



# =========================================================
# TARGETED BILINGUAL / PLACEHOLDER HANDLING
# =========================================================

def _is_label_only_value(value):
    if value is None:
        return True

    v = str(value).strip()
    if not v:
        return True

    # Pure Chinese text is a translated label, not a field value.
    if re.search(r"[\u4e00-\u9fff]", v) and not re.search(r"[A-Za-z0-9]", v):
        return True

    n = re.sub(r"\s+", " ", v).strip().lower()
    n = n.strip(" :|-.()")

    return n in {
        "principal or seller",
        "party",
        "party/intermediate consignee",
        "notify party",
        "notify party/intermediate consignee",
        "notify",
        "pol",
        "pod",
        "shipper",
        "consignee",
        "port of loading",
        "port of discharge",
        "load port",
        "discharge port",
        "no. of containers",
        "no of containers",
        "total containers",
        "container count",
        "total container",
    }


def _clean_candidate(value):
    if value is None:
        return None

    raw = str(value).strip()

    # For bilingual "label | actual value", discard only the
    # label/translation side. Normal address pipes keep baseline behavior.
    if "|" in raw:
        parts = [p.strip() for p in raw.split("|")]
        if parts and _is_label_only_value(parts[0]):
            for part in parts[1:]:
                if part and not _is_label_only_value(part):
                    return clean_value(part)
        return clean_value(raw)

    if _is_label_only_value(raw):
        return None

    return clean_value(raw)


# =========================================================
# INLINE EXTRACTION
# =========================================================

def find_inline_value(text, labels):
    if not text:
        return None

    lines = str(text).splitlines()

    # IMPORTANT:
    # Check longest labels first.
    #
    # Example:
    # Notify Party/Intermediate Consignee
    # must be checked before:
    # Notify Party
    # and Notify

    sorted_labels = sorted(
        labels,
        key=len,
        reverse=True
    )

    for line in lines:
        line = line.strip()

        if not line:
            continue

        for label in sorted_labels:
            pattern = re.escape(label)

            # Handles:
            # Label | Value
            # Label: Value
            # Label - Value
            # Label Value

            match = re.match(
                rf"^\s*{pattern}(?:\s*(?:\:|\||\-)\s*|\s+)(.+?)\s*$",
                line,
                flags=re.IGNORECASE
            )

            if match:
                value = _clean_candidate(match.group(1))

                if value:
                    return value

    return None


# =========================================================
# SAME LINE EXTRACTION
# =========================================================

def find_same_line_value(text, labels):
    if not text:
        return None

    lines = str(text).splitlines()

    sorted_labels = sorted(
        labels,
        key=len,
        reverse=True
    )

    for line in lines:
        original = line.strip()

        if not original:
            continue

        simplified = simplify_label(original)

        for label in sorted_labels:
            label_simple = simplify_label(label)

            if simplified.startswith(label_simple):

                pattern = re.escape(label)

                match = re.match(
                    rf"^\s*{pattern}(?:\s*(?:\:|\||\-)\s*|\s+)(.*?)\s*$",
                    original,
                    flags=re.IGNORECASE
                )

                if match:
                    value = _clean_candidate(match.group(1))

                    if value:
                        return value

    return None


# =========================================================
# MULTI-LINE EXTRACTION
# =========================================================

def find_multiline_value(text, labels):
    if not text:
        return None

    lines = str(text).splitlines()

    for index, line in enumerate(lines):
        line = line.strip()

        if not line:
            continue

        if label_matches(line, labels):

            for next_line in lines[index + 1:]:
                next_line = next_line.strip()

                if not next_line:
                    continue

                if is_any_known_label(next_line):
                    break

                # Skip translated/placeholder labels and keep looking.
                if _is_label_only_value(next_line):
                    continue

                value = _clean_candidate(next_line)

                if value:
                    return value

    return None


# =========================================================
# GENERAL VALUE EXTRACTION
# =========================================================

def find_value(text, labels):
    if not text:
        return None

    # 1. Label | Value
    value = find_inline_value(text, labels)

    if value:
        return value

    # 2. Label: Value / Label Value
    value = find_same_line_value(text, labels)

    if value:
        return value

    # 3. Label on one line, value on next line
    value = find_multiline_value(text, labels)

    if value:
        return value

    return None


# =========================================================
# FIELD EXTRACTORS
# =========================================================

def extract_shipper(text):
    return find_value(
        text,
        SHIPPER_LABELS
    )


def extract_consignee(text):
    return find_value(
        text,
        CONSIGNEE_LABELS
    )


def extract_notify_party(text):
    if not text:
        return None

    lines = str(text).splitlines()

    # Check longest/specific notify labels first
    sorted_labels = sorted(
        NOTIFY_LABELS,
        key=len,
        reverse=True
    )

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Excel / structured format
        #
        # Notify Party | ABC COMPANY
        # Notify Party/Intermediate Consignee | ABC COMPANY

        if "|" in line:
            parts = line.split("|", 1)

            label = parts[0].strip()
            value = parts[1].strip()

            if label_matches(label, NOTIFY_LABELS):
                return _clean_candidate(value)

        # Word / TXT format
        for label in sorted_labels:

            simplified_line = simplify_label(line)
            simplified_label = simplify_label(label)

            if simplified_line.startswith(
                simplified_label
            ):

                pattern = re.escape(label)

                match = re.match(
                    rf"^\s*{pattern}(?:\s*(?:\:|\-)\s*|\s+)(.*?)\s*$",
                    line,
                    flags=re.IGNORECASE
                )

                if match:
                    value = _clean_candidate(match.group(1))

                    if value:
                        return value

    # Generic fallback
    return find_value(
        text,
        NOTIFY_LABELS
    )


def extract_port_of_loading(text):
    return find_value(
        text,
        POL_LABELS
    )


def extract_port_of_discharge(text):
    return find_value(
        text,
        POD_LABELS
    )


def extract_container_count(text):
    value = find_value(
        text,
        CONTAINER_LABELS
    )

    if value is None:
        return None

    return clean_value(value)


# =========================================================
# GROSS WEIGHT
# =========================================================

def extract_gross_weight(text):
    if not text:
        return None

    lines = str(text).splitlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # -------------------------------------------------
        # Excel format
        #
        # Gross Weight (KG) | 100445
        # GROSS WEIGHT | 216950
        # Gross Weightæ¯›é‡(KGS) | 328665
        # -------------------------------------------------

        if "|" in line:

            parts = line.split("|", 1)

            label = parts[0].strip()
            value = parts[1].strip()

            if label_matches(
                label,
                WEIGHT_LABELS
            ):

                value = value.replace(",", "")

                match = re.search(
                    r"\d+(?:\.\d+)?",
                    value
                )

                if match:
                    return match.group(0)

        # -------------------------------------------------
        # Word / TXT format
        # -------------------------------------------------

        for label in sorted(
            WEIGHT_LABELS,
            key=len,
            reverse=True
        ):

            pattern = re.escape(label)

            match = re.match(
                rf"^\s*{pattern}\s*(?:\:|\-)?\s*(.*?)\s*$",
                line,
                flags=re.IGNORECASE
            )

            if match:

                value = match.group(1)

                value = value.replace(",", "")

                match_number = re.search(
                    r"\d+(?:\.\d+)?",
                    value
                )

                if match_number:
                    return match_number.group(0)

        # -------------------------------------------------
        # Generic normalized detection
        # -------------------------------------------------

        simplified_line = simplify_label(line)

        if (
            simplified_line.startswith("gross weight")
            or simplified_line.startswith("gross wt")
        ):

            numbers = re.findall(
                r"\d+(?:,\d{3})*(?:\.\d+)?",
                line
            )

            if numbers:
                return numbers[-1].replace(",", "")

    return None


# =========================================================
# MAIN EXTRACTION
# =========================================================

def extract_fields(text):

    fields = {
        "shipper": extract_shipper(text),

        "consignee": extract_consignee(text),

        "notify_party": extract_notify_party(text),

        "port_of_loading": extract_port_of_loading(text),

        "port_of_discharge": extract_port_of_discharge(text),

        "container_count": extract_container_count(text),

        "gross_weight_kg": extract_gross_weight(text)
    }

    return fields


# =========================================================
# MISSING FIELD CHECK
# =========================================================

def get_missing_fields(fields):

    return [
        field
        for field in REQUIRED_FIELDS
        if fields.get(field) is None
    ]


def has_all_required_fields(fields):

    return len(
        get_missing_fields(fields)
    ) == 0


# =========================================================
# DEBUG PRINT
# =========================================================

def print_extracted_fields(fields):

    print("\n=== EXTRACTED FIELDS ===")

    for field in REQUIRED_FIELDS:

        value = fields.get(field)

        if value is None:
            print(
                f"{field}: MISSING"
            )
        else:
            print(
                f"{field}: {value}"
            )
