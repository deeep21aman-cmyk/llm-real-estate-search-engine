from RealtorDR.app.config import IGNORE_EXPLANATION_TERMS


def generate_explanation(parsed, keywords, row, result_type):

    reasons = []

    bedrooms = row[3]
    price = row[2]
    embedding_text = (row[8] or "").lower()
    title = (row[1] or "").lower()
    address = (row[6] or "").lower()

    down_payment_amount = row[10]
    down_payment_percent = row[11]

    # -----------------------
    # Bedroom explanations
    # -----------------------
    if parsed["bedrooms"] and bedrooms == parsed["bedrooms"]:
        reasons.append(f"✓ Property has {bedrooms} bedrooms as requested")

    if parsed["min_bedrooms"] and bedrooms >= parsed["min_bedrooms"]:
        reasons.append(f"✓ Property has at least {parsed['min_bedrooms']} bedrooms")

    if parsed["max_bedrooms"] and bedrooms <= parsed["max_bedrooms"]:
        reasons.append(f"✓ Property has no more than {parsed['max_bedrooms']} bedrooms")

    # -----------------------
    # Price explanations
    # -----------------------
    if parsed["max_price"] and price <= parsed["max_price"]:
        reasons.append(f"✓ Property price is under ${parsed['max_price']}")

    if parsed["min_price"] and price >= parsed["min_price"]:
        reasons.append(f"✓ Property price is above ${parsed['min_price']}")

    # -----------------------
    # Location explanations
    # -----------------------
    if parsed.get("location"):
        loc = parsed["location"].lower()
        if loc in address:
            reasons.append(f"✓ Property is located in {parsed['location'].title()}")

    elif parsed.get("location_keywords"):
        matched_location = False
        for loc in parsed["location_keywords"]:
            if loc.lower() in address:
                reasons.append(f"✓ Property is located in {loc.title()}")
                matched_location = True
                break

    # -----------------------
    # Feature explanations
    # -----------------------
    for feature in parsed["feature_names"]:
        if feature in embedding_text or feature in title:
            reasons.append(f"✓ Property has {feature}")

    # -----------------------
    # Keyword explanations
    # -----------------------

    matched_keywords = []
    missing_keywords = []

    for word in keywords:

        # ignore generic words like house/villa/property
        if word in IGNORE_EXPLANATION_TERMS:
            continue

        # ignore location tokens
        if parsed.get("location_keywords") and word in parsed["location_keywords"]:
            continue

        # direct keyword match
        if word in embedding_text or word in title:
            matched_keywords.append(word)

        # semantic beach/ocean handling
        elif "beach" in word:
            if (
                "beach" in embedding_text
                or "beach" in title
                or "beachfront" in embedding_text
                or "beachfront" in title
                or "ocean" in embedding_text
                or "ocean" in title
                or "ocean view" in embedding_text
                or "ocean view" in title
            ):
                matched_keywords.append(word)
            else:
                missing_keywords.append(word)

        else:
            missing_keywords.append(word)

    if matched_keywords:
        keywords_str = ", ".join(matched_keywords)
        reasons.append(f"✓ Property matches your search for {keywords_str}")

    if missing_keywords and result_type == "additional":
        missing_str = ", ".join(missing_keywords)
        reasons.append(
            f"✓ Property appears semantically related to your search for {missing_str}"
        )

    # -----------------------
    # Down payment percent
    # -----------------------
    if (
        parsed["min_down_payment_percent"]
        and down_payment_percent
        and down_payment_percent >= parsed["min_down_payment_percent"]
    ):
        reasons.append(
            f"✓ Down payment {down_payment_percent}% meets requested minimum"
        )

    if (
        parsed["max_down_payment_percent"]
        and down_payment_percent
        and down_payment_percent <= parsed["max_down_payment_percent"]
    ):
        reasons.append(
            f"✓ Down payment {down_payment_percent}% is within requested range"
        )

    # -----------------------
    # Down payment amount
    # -----------------------
    if (
        parsed["min_down_payment_amount"]
        and down_payment_amount
        and down_payment_amount >= parsed["min_down_payment_amount"]
    ):
        reasons.append(
            f"✓ Down payment amount ${down_payment_amount} meets requested minimum"
        )

    if (
        parsed["max_down_payment_amount"]
        and down_payment_amount
        and down_payment_amount <= parsed["max_down_payment_amount"]
    ):
        reasons.append(
            f"✓ Down payment amount ${down_payment_amount} is within requested range"
        )

    return reasons
