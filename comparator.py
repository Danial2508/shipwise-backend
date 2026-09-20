import re


# =========================================================
# GENERAL NORMALIZATION
# =========================================================

def normalize(value):

    if value is None:
        return None

    value = str(value).strip().lower()

    # Replace multiple spaces
    value = re.sub(r"\s+", " ", value)

    # Normalize common punctuation
    value = value.replace("\r", " ")
    value = value.replace("\n", " ")

    # Remove spaces around punctuation
    value = re.sub(r"\s*,\s*", ", ", value)

    return value.strip()


# =========================================================
# PARTY / COMPANY NORMALIZATION
# =========================================================

def normalize_party(value):

    value = normalize(value)

    if value is None:
        return None

    # Sometimes extraction may still contain an address.
    # Keep company/name before "|".
    if "|" in value:
        value = value.split("|")[0].strip()

    # Normalize punctuation
    value = value.replace(".", "")
    value = value.replace(",", " ")

    # Remove duplicate spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# =========================================================
# PORT NORMALIZATION
# =========================================================

def normalize_port(value):

    value = normalize(value)

    if value is None:
        return None

    # Remove common port labels
    prefixes = [
        "port of loading",
        "port of discharge",
        "loading port",
        "load port",
        "discharge port",
        "pod",
        "pol"
    ]

    for prefix in prefixes:

        if value.startswith(prefix):
            value = value[len(prefix):].strip()

    # Remove punctuation
    value = value.replace(",", " ")
    value = value.replace(".", " ")

    # Normalize spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# =========================================================
# CONTAINER NORMALIZATION
# =========================================================

def normalize_container(value):

    value = normalize(value)

    if value is None:
        return None

    # Examples:
    #
    # 15 x 20'GP
    # 15X20'GP
    # 15 x 20 GP
    #
    # Normalize X spacing and apostrophe.

    value = value.replace("×", "x")

    value = re.sub(
        r"\s*x\s*",
        " x ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    # Normalize common container notation
    value = value.replace("'", "")

    return value.strip()


# =========================================================
# WEIGHT NORMALIZATION
# =========================================================

def normalize_weight(value):

    if value is None:
        return None

    try:

        text = str(value).strip().lower()

        # Remove commas
        text = text.replace(",", "")

        # Remove KG
        text = re.sub(
            r"\bkg\b",
            "",
            text
        )

        # Remove spaces
        text = text.strip()

        return float(text)

    except (ValueError, TypeError):

        # Try extracting number if there is extra text
        try:

            text = str(value).replace(",", "")

            match = re.search(
                r"\d+(?:\.\d+)?",
                text
            )

            if match:
                return float(match.group(0))

        except Exception:
            pass

    return None


# =========================================================
# FIELD-SPECIFIC NORMALIZATION
# =========================================================

def normalize_field(field, value):

    if field in [
        "shipper",
        "consignee",
        "notify_party"
    ]:
        return normalize_party(value)

    if field in [
        "port_of_loading",
        "port_of_discharge"
    ]:
        return normalize_port(value)

    if field == "container_count":
        return normalize_container(value)

    if field == "gross_weight_kg":
        return normalize_weight(value)

    return normalize(value)


# =========================================================
# COMPARE DOCUMENTS
# =========================================================

def compare_documents(si_fields, bl_fields):

    defect_fields = []

    differences = {}

    required_fields = [
        "shipper",
        "consignee",
        "notify_party",
        "port_of_loading",
        "port_of_discharge",
        "container_count",
        "gross_weight_kg"
    ]

    # -----------------------------------------------------
    # Compare all 7 required fields
    # -----------------------------------------------------

    for field in required_fields:

        si_value = si_fields.get(field)
        bl_value = bl_fields.get(field)

        si_normalized = normalize_field(
            field,
            si_value
        )

        bl_normalized = normalize_field(
            field,
            bl_value
        )

        # -------------------------------------------------
        # Missing value
        # -------------------------------------------------

        if (
            si_normalized is None
            or bl_normalized is None
        ):

            defect_fields.append(field)

            differences[field] = {
                "si_value": si_value,
                "bl_value": bl_value,
                "reason": "missing_value"
            }

            continue

        # -------------------------------------------------
        # Actual mismatch
        # -------------------------------------------------

        if si_normalized != bl_normalized:

            defect_fields.append(field)

            differences[field] = {
                "si_value": si_value,
                "bl_value": bl_value,
                "reason": "mismatch"
            }

    # -----------------------------------------------------
    # Final result
    # -----------------------------------------------------

    if defect_fields:

        return {
            "status": "MISMATCH",
            "has_defect": True,
            "defect_fields": defect_fields,
            "differences": differences
        }

    return {
        "status": "OK",
        "has_defect": False,
        "defect_fields": [],
        "differences": {}
    }


# =========================================================
# DEBUG COMPARISON
# =========================================================

def print_comparison(si_fields, bl_fields, result):

    print("\n==============================")
    print("DOCUMENT COMPARISON")
    print("==============================")

    fields = [
        "shipper",
        "consignee",
        "notify_party",
        "port_of_loading",
        "port_of_discharge",
        "container_count",
        "gross_weight_kg"
    ]

    for field in fields:

        si_value = si_fields.get(field)
        bl_value = bl_fields.get(field)

        print(f"\n{field}")
        print(f"  SI: {si_value}")
        print(f"  BL: {bl_value}")

    print("\nSTATUS:")
    print(result["status"])

    if result["defect_fields"]:

        print("\nDEFECT FIELDS:")

        for field in result["defect_fields"]:
            print(f"- {field}")

    print("==============================\n")