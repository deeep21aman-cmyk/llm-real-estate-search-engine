import numpy as np


def coerce_number(value):
    if value is None:
        return None
    return float(value)

def coerce_embedding(value):
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        return value
    if isinstance(value, (list, tuple)):
        return np.array(value, dtype=float)
    if isinstance(value, str):
        stripped = value.strip()[1:-1]
        if not stripped:
            return None
        return np.fromstring(stripped, sep=",", dtype=float)
    return np.array(value, dtype=float)

def cosine_similarity(a, b):

    a = coerce_embedding(a)
    b = coerce_embedding(b)

    if a is None or b is None or a.size == 0 or b.size == 0:
        return 0.0

    denom = (np.linalg.norm(a) * np.linalg.norm(b))

    if denom == 0:
        return 0.0

    return np.dot(a, b) / denom


def score_exact_match(actual, target, reward, penalty):
    if target is None:
        return 0.0, True
    if actual is None:
        return -penalty, False
    if actual == target:
        return reward, True
    return -(penalty + abs(actual - target)), False


def score_min_constraint(actual, minimum, reward, penalty_scale=1.0):
    if minimum is None:
        return 0.0, True
    if actual is None:
        return -reward, False
    if actual >= minimum:
        return reward, True
    shortfall = minimum - actual
    return -(shortfall * penalty_scale), False


def score_max_constraint(actual, maximum, reward, penalty_scale=1.0):
    if maximum is None:
        return 0.0, True
    if actual is None:
        return -reward, False
    if actual <= maximum:
        return reward, True
    overflow = actual - maximum
    return -(overflow * penalty_scale), False


def rank_results(search_results, query_embedding, parsed):

    scored_results = []

    for r in search_results:

        property_embedding = r[9]
        structured_score = float(r[12] or 0.0)
        vector_score = r[13] if len(r) > 13 else None

        bedrooms = coerce_number(r[3])
        bathrooms = coerce_number(r[4])
        price = coerce_number(r[2])
        size = coerce_number(r[5])
        address = (r[6] or "").lower()
        title = (r[1] or "").lower()
        down_payment_amount = coerce_number(r[10])
        down_payment_percent = coerce_number(r[11])

        # -----------------------
        # Semantic similarity
        # -----------------------
        semantic_score = float(vector_score) if vector_score is not None else cosine_similarity(query_embedding, property_embedding)

        # -----------------------
        # Unified structured constraint scoring
        # -----------------------
        constraint_score = structured_score
        valid_match = True

        score, matched = score_exact_match(bedrooms, parsed.get("bedrooms"), reward=6, penalty=6)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_min_constraint(bedrooms, parsed.get("min_bedrooms"), reward=1.5)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_max_constraint(bedrooms, parsed.get("max_bedrooms"), reward=1.5)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_exact_match(bathrooms, parsed.get("bathrooms"), reward=3, penalty=3)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_min_constraint(bathrooms, parsed.get("min_bathrooms"), reward=1.0, penalty_scale=0.5)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_max_constraint(bathrooms, parsed.get("max_bathrooms"), reward=1.0, penalty_scale=0.5)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_min_constraint(price, parsed.get("min_price"), reward=1.0, penalty_scale=1 / max(parsed.get("min_price") or 1, 1))
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_max_constraint(price, parsed.get("max_price"), reward=2.0, penalty_scale=2 / max(parsed.get("max_price") or 1, 1))
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_min_constraint(size, parsed.get("min_size"), reward=1.5, penalty_scale=0.05)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_max_constraint(size, parsed.get("max_size"), reward=1.5, penalty_scale=0.05)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_min_constraint(down_payment_amount, parsed.get("min_down_payment_amount"), reward=1.0, penalty_scale=0.001)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_max_constraint(down_payment_amount, parsed.get("max_down_payment_amount"), reward=1.0, penalty_scale=0.001)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_min_constraint(down_payment_percent, parsed.get("min_down_payment_percent"), reward=1.0, penalty_scale=0.2)
        constraint_score += score
        valid_match = valid_match and matched

        score, matched = score_max_constraint(down_payment_percent, parsed.get("max_down_payment_percent"), reward=1.0, penalty_scale=0.2)
        constraint_score += score
        valid_match = valid_match and matched

        # -----------------------
        # Feature scoring
        # -----------------------
        for feature in parsed.get("feature_names", []):

            if feature in title:
                constraint_score += 2

        # -----------------------
        # Location scoring
        # -----------------------
        if parsed.get("location"):
            if parsed["location"].lower() in address:
                constraint_score += 2
            else:
                constraint_score -= 2
                valid_match = False

        # -----------------------
        # Final hybrid score
        # -----------------------
        semantic_weight = 0.3
        if valid_match:
            semantic_weight = 1.2

        score = constraint_score + (semantic_score * semantic_weight)

        # Bonus when both semantic and structured signals are strong
        if semantic_score > 0.75 and constraint_score > 2:
            score += 1.0

        scored_results.append((score, r))

    scored_results.sort(reverse=True, key=lambda x: x[0])

    return scored_results
