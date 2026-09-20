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

    value = str(value).strip()

    # If pipe exists, take value before extra columns
    if "|" in value:
        value = value.split("|", 1)[0].strip()

    # Remove excessive spaces
    value = re.sub(r"\s+", " ", value)

    value = value.strip(" ;,:|")

    invalid_values = {
        "",
        "n/a",
        "na",
        "n.a.",
        "tba",
        "tbc",
        "unknown",
        "unknown.",
        "______",
        "-------",
        "___",
        "??",
        "???"
    }

    if value.lower() in invalid_values:
        return None

    return value


# =========================================================
# SIMPLIFY LABEL
#
# Examples:
#
# Shipper (Principal or Seller)
# -> Shipper
#
# Shipper (发货人)
# -> Shipper
#
# Port of Loading (POL) (装货港)
# -> Port of Loading
# =========================================================

def simplify_label(label):

    if not label:
        return ""

    label = str(label).strip()

    previous = None

    while previous != label:

        previous = label

        label = re.sub(
            r"\s*\([^()]*\)",
            "",
            label
        )

    # Remove excessive whitespace
    label = re.sub(
        r"\s+",
        " ",
        label
    )

    return label.strip()


# =========================================================
# KNOWN LABELS
# =========================================================

KNOWN_LABELS = [
    "shipper/exporter",
    "shipper",

    "consignee",

    "notify party/intermediate consignee",
    "notify party",
    "notify",

    "port of loading",
    "loading port",
    "load port",
    "pol",

    "port of discharge",
    "discharge port",
    "pod",

    "total containers",
    "container count",
    "no. of containers or packages",
    "no. of containers",
    "number of containers",

    "gross weight",
    "gross wt"
]


# =========================================================
# CHECK WHETHER LINE IS A KNOWN LABEL
# =========================================================

def is_any_known_label(line):

    if not line:
        return False

    simplified = simplify_label(
        line
    ).lower()

    return simplified in KNOWN_LABELS


# =========================================================
# INLINE LABEL MATCH
#
# Handles:
#
# Shipper: ABC
# Shipper | ABC
# Shipper (发货人) | ABC
# =========================================================

def label_matches(line, labels):

    if not line:
        return None

    cleaned_line = line.strip()

    # ---------------------------------------------
    # Colon format
    # ---------------------------------------------

    if ":" in cleaned_line:

        possible_label, value = (
            cleaned_line.split(":", 1)
        )

    # ---------------------------------------------
    # Pipe format
    # ---------------------------------------------

    elif "|" in cleaned_line:

        possible_label, value = (
            cleaned_line.split("|", 1)
        )

    else:

        return None

    possible_label = simplify_label(
        possible_label
    ).lower()

    for label in labels:

        target = simplify_label(
            label
        ).lower()

        if possible_label == target:

            return clean_value(
                value
            )

    return None


# =========================================================
# FIND INLINE VALUE
# =========================================================

def find_inline_value(text, labels):

    if not text:
        return None

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        value = label_matches(
            line,
            labels
        )

        if value is not None:

            return value

    return None


# =========================================================
# FIND MULTILINE VALUE
#
# Example:
#
# Shipper
# ABC COMPANY
#
# Consignee
# XYZ COMPANY
# =========================================================

def find_multiline_value(text, labels):

    if not text:
        return None

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        simplified_line = simplify_label(
            line
        ).lower()

        for label in labels:

            target = simplify_label(
                label
            ).lower()

            if simplified_line != target:
                continue

            # Look ahead a few lines
            for next_index in range(
                index + 1,
                min(index + 4, len(lines))
            ):

                candidate = lines[
                    next_index
                ]

                # Stop if another known label appears
                if is_any_known_label(
                    candidate
                ):
                    break

                # Ignore decorative lines
                if candidate in [
                    "|",
                    "-",
                    "_",
                    "—"
                ]:
                    continue

                value = clean_value(
                    candidate
                )

                if value:

                    return value

    return None


# =========================================================
# FIND SAME-LINE VALUE
#
# Handles PDF:
#
# Shipper (Principal or Seller) ABC COMPANY
#
# Notify INTERNATIONAL FOREST PRODUCTS LLC
#
# Load Port RUGAO/NANTONG/SHANGHAI, CHINA
#
# Discharge Port CONAKRY, GUINEA
# =========================================================

def find_same_line_value(text, labels):

    if not text:
        return None

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # Sort longest labels first.
    # This prevents "Notify" from matching
    # "Notify Party/Intermediate Consignee".
    sorted_labels = sorted(
        labels,
        key=len,
        reverse=True
    )

    for line in lines:

        original_line = line

        for label in sorted_labels:

            # -------------------------------------------------
            # Build regex which allows bracketed descriptions
            #
            # Example:
            # Shipper (Principal or Seller) ABC
            #
            # Shipper (发货人) ABC
            # -------------------------------------------------

            label_pattern = re.escape(
                label
            )

            pattern = (
                rf"^\s*"
                rf"{label_pattern}"
                rf"(?:\s*\([^)]*\))*"
                rf"\s+"
                rf"(.+?)"
                rf"\s*$"
            )

            match = re.match(
                pattern,
                original_line,
                re.IGNORECASE
            )

            if not match:
                continue

            value = match.group(
                1
            ).strip()

            # Remove any remaining bracket descriptors
            while True:

                new_value = re.sub(
                    r"^\s*\([^()]*\)\s*",
                    "",
                    value
                )

                if new_value == value:
                    break

                value = new_value

            value = clean_value(
                value
            )

            if value:

                return value

    return None


# =========================================================
# GENERAL FIELD FINDER
#
# Search order:
#
# 1. label:value
# 2. label|value
# 3. label + next line
# 4. label + value same line
# =========================================================

def find_value(text, labels):

    if not text:
        return None

    # 1. Inline colon / pipe
    value = find_inline_value(
        text,
        labels
    )

    if value is not None:
        return value

    # 2. Multiline
    value = find_multiline_value(
        text,
        labels
    )

    if value is not None:
        return value

    # 3. Same-line PDF format
    value = find_same_line_value(
        text,
        labels
    )

    if value is not None:
        return value

    return None


# =========================================================
# SHIPPER
# =========================================================

def extract_shipper(text):

    return find_value(
        text,
        [
            "Shipper/Exporter",
            "Shipper"
        ]
    )


# =========================================================
# CONSIGNEE
# =========================================================

def extract_consignee(text):

    value = find_value(
        text,
        [
            "Consignee",
            "To the Order of"
        ]
    )

    return value

# =========================================================
# NOTIFY PARTY
# =========================================================

def extract_notify_party(text):

    value = find_value(
        text,
        [
            "Notify Party/Intermediate Consignee",
            "Notify Party",
            "Notify",
            "Party/Intermediate Consignee"
        ]
    )

    if value is None:
        return None

    # -------------------------------------------------
    # Remove accidental label prefix
    #
    # Example:
    # Party/Intermediate ConsigneeCERIEX
    # -> CERIEX
    #
    # Notify Party/Intermediate ConsigneeABC
    # -> ABC
    # -------------------------------------------------

    value = re.sub(
        r"^party\s*/\s*intermediate\s*consignee",
        "",
        value,
        flags=re.IGNORECASE
    ).strip()

    value = re.sub(
        r"^notify\s*party\s*/\s*intermediate\s*consignee",
        "",
        value,
        flags=re.IGNORECASE
    ).strip()

    value = re.sub(
        r"^notify\s*party",
        "",
        value,
        flags=re.IGNORECASE
    ).strip()

    value = re.sub(
        r"^notify\b",
        "",
        value,
        flags=re.IGNORECASE
    ).strip()

    return clean_value(value)


# =========================================================
# PORT OF LOADING
# =========================================================

def extract_port_of_loading(text):

    return find_value(
        text,
        [
            "Port of Loading",
            "Loading Port",
            "Load Port",
            "POL"
        ]
    )


# =========================================================
# PORT OF DISCHARGE
# =========================================================

def extract_port_of_discharge(text):

    return find_value(
        text,
        [
            "Port of Discharge",
            "Discharge Port",
            "POD"
        ]
    )


# =========================================================
# CONTAINER COUNT
# =========================================================

def extract_container_count(text):

    return find_value(
        text,
        [
            "Total Containers",
            "Container Count",
            "No. of Containers or Packages",
            "No. of Containers",
            "Number of Containers"
        ]
    )


# =========================================================
# GROSS WEIGHT
#
# Handles:
#
# Gross Weight (KG): 41,604 KG
#
# Gross Weight毛重(KGS): 41,604 KG
#
# TOTAL Gross Weight■■(KGS): 41,604 KG
#
# Gross Wt (kgs) (毛重 KGS) | 100445
# =========================================================

def extract_gross_weight(text):

    if not text:
        return None

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Never use NET weight
        if "net weight" in line.lower():
            continue

        # Must contain Gross Weight / Gross Wt
        if not re.search(
            r"gross\s*(?:weight|wt)",
            line,
            re.IGNORECASE
        ):
            continue

        # ---------------------------------------------
        # Extract value after pipe
        # ---------------------------------------------

        if "|" in line:

            value_part = line.split(
                "|",
                1
            )[1].strip()

        # ---------------------------------------------
        # Extract value after colon
        # ---------------------------------------------

        elif ":" in line:

            value_part = line.split(
                ":",
                1
            )[1].strip()

        # ---------------------------------------------
        # Otherwise find number directly
        # ---------------------------------------------

        else:

            match = re.search(
                r"\d[\d,\s]*(?:\.\d+)?",
                line,
                re.IGNORECASE
            )

            if not match:
                continue

            value_part = match.group(
                0
            )

        # Invalid values
        if re.search(
            r"\b(?:N/?A|TBA|TBC)\b",
            value_part,
            re.IGNORECASE
        ):
            return None

        if re.search(
            r"[_?]{2,}",
            value_part
        ):
            return None

        # Extract number
        match = re.search(
            r"\d[\d,\s]*(?:\.\d+)?",
            value_part
        )

        if not match:
            continue

        number = match.group(
            0
        )

        number = (
            number
            .replace(",", "")
            .replace(" ", "")
        )

        try:

            return float(
                number
            )

        except ValueError:

            continue

    return None


# =========================================================
# EXTRACT ALL 7 FIELDS
# =========================================================

def extract_fields(text):

    fields = {}

    fields["shipper"] = extract_shipper(
        text
    )

    fields["consignee"] = extract_consignee(
        text
    )

    fields["notify_party"] = extract_notify_party(
        text
    )

    fields["port_of_loading"] = extract_port_of_loading(
        text
    )

    fields["port_of_discharge"] = extract_port_of_discharge(
        text
    )

    fields["container_count"] = extract_container_count(
        text
    )

    fields["gross_weight_kg"] = extract_gross_weight(
        text
    )

    return fields


# =========================================================
# MISSING FIELDS
# =========================================================

def get_missing_fields(fields):

    missing = []

    for field in REQUIRED_FIELDS:

        if fields.get(field) is None:

            missing.append(
                field
            )

    return missing


# =========================================================
# CHECK ALL REQUIRED FIELDS
# =========================================================

def has_all_required_fields(fields):

    return len(
        get_missing_fields(fields)
    ) == 0


# =========================================================
# DEBUG PRINT
# =========================================================

def print_extracted_fields(fields):

    print(
        "\n=== EXTRACTED SHIPPING FIELDS ==="
    )

    for field in REQUIRED_FIELDS:

        print(
            f"{field}: "
            f"{fields.get(field)}"
        )

    missing = get_missing_fields(
        fields
    )

    if missing:

        print(
            "\nMissing fields:"
        )

        for field in missing:

            print(
                f"- {field}"
            )

    else:

        print(
            "\nAll 7 required fields extracted."
        )

    print(
        "=================================\n"
    )