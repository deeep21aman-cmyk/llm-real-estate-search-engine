import numpy as np
import re


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


def tokenize_text(*parts):
    text = " ".join(str(part or "").lower() for part in parts)
    return set(re.findall(r"[a-z0-9]+", text))


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


def score_preference_presence(text_blob, phrases, reward):
    score = 0.0
    matches = 0

    for phrase in phrases or []:
        cleaned = phrase.strip().lower()
        if cleaned and cleaned in text_blob:
            score += reward
            matches += 1

    return score, matches


def apply_diversity_rerank(scored_results):
    reranked = []
    selected_token_sets = []

    for base_score, row in sorted(scored_results, reverse=True, key=lambda x: x[0]):
        token_set = tokenize_text(row[1], row[6])
        diversity_penalty = 0.0

        for existing_tokens in selected_token_sets:
            union = token_set | existing_tokens
            if not union:
                continue
            overlap = len(token_set & existing_tokens) / len(union)
            diversity_penalty = max(diversity_penalty, overlap)

        adjusted_score = base_score - (diversity_penalty * 0.8)
        reranked.append((adjusted_score, row))
        selected_token_sets.append(token_set)

    reranked.sort(reverse=True, key=lambda x: x[0])
    return reranked


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
        embedding_text = (r[8] or "").lower()
        text_blob = " ".join(part for part in [title, address, embedding_text] if part)

        # -----------------------
        # Semantic similarity
        # -----------------------
        semantic_score = float(vector_score) if vector_score is not None else cosine_similarity(query_embedding, property_embedding)

        # -----------------------
        # Unified structured constraint scoring
        # -----------------------
        constraint_score = structured_score * 0.55
        miss_count = 0

        score, matched = score_exact_match(bedrooms, parsed.get("bedrooms"), reward=6, penalty=6)
        constraint_score += score * 0.45
        miss_count += 0 if matched else 1

        score, matched = score_min_constraint(bedrooms, parsed.get("min_bedrooms"), reward=1.5)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_max_constraint(bedrooms, parsed.get("max_bedrooms"), reward=1.5)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_exact_match(bathrooms, parsed.get("bathrooms"), reward=3, penalty=3)
        constraint_score += score * 0.5
        miss_count += 0 if matched else 1

        score, matched = score_min_constraint(bathrooms, parsed.get("min_bathrooms"), reward=1.0, penalty_scale=0.5)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_max_constraint(bathrooms, parsed.get("max_bathrooms"), reward=1.0, penalty_scale=0.5)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_min_constraint(price, parsed.get("min_price"), reward=1.0, penalty_scale=1 / max(parsed.get("min_price") or 1, 1))
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_max_constraint(price, parsed.get("max_price"), reward=2.0, penalty_scale=2 / max(parsed.get("max_price") or 1, 1))
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_min_constraint(size, parsed.get("min_size"), reward=1.5, penalty_scale=0.05)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_max_constraint(size, parsed.get("max_size"), reward=1.5, penalty_scale=0.05)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_min_constraint(down_payment_amount, parsed.get("min_down_payment_amount"), reward=1.0, penalty_scale=0.001)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_max_constraint(down_payment_amount, parsed.get("max_down_payment_amount"), reward=1.0, penalty_scale=0.001)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_min_constraint(down_payment_percent, parsed.get("min_down_payment_percent"), reward=1.0, penalty_scale=0.2)
        constraint_score += score
        miss_count += 0 if matched else 1

        score, matched = score_max_constraint(down_payment_percent, parsed.get("max_down_payment_percent"), reward=1.0, penalty_scale=0.2)
        constraint_score += score
        miss_count += 0 if matched else 1

        # -----------------------
        # Feature scoring
        # -----------------------
        feature_score, matched_features = score_preference_presence(
            text_blob,
            parsed.get("feature_names", []),
            reward=2.4,
        )
        constraint_score += feature_score

        # -----------------------
        # Location scoring
        # -----------------------
        if parsed.get("location"):
            if parsed["location"].lower() in address:
                constraint_score += 3
            else:
                constraint_score -= 1.5
                miss_count += 1

        for loc in parsed.get("location_keywords", []):
            if loc.lower() in text_blob:
                constraint_score += 0.8

        # -----------------------
        # Unknown term intent scoring
        # -----------------------
        unknown_term_score, matched_unknown_terms = score_preference_presence(
            text_blob,
            parsed.get("unknown_terms", []),
            reward=1.2,
        )
        constraint_score += unknown_term_score

        semantic_intent_score = 0.0
        if parsed.get("unknown_terms"):
            semantic_intent_score += semantic_score * min(len(parsed["unknown_terms"]), 3) * 1.1
            if matched_unknown_terms == 0 and semantic_score > 0.68:
                semantic_intent_score += 0.75

        if parsed.get("feature_names") and matched_features == 0 and semantic_score > 0.72:
            semantic_intent_score += 0.5

        # -----------------------
        # Final hybrid score
        # -----------------------
        semantic_weight = max(1.4, 2.6 - (0.15 * miss_count))

        score = constraint_score + semantic_intent_score + (semantic_score * semantic_weight)

        # Bonus when both semantic and structured signals are strong
        if semantic_score > 0.75 and constraint_score > 2:
            score += 1.25
        if semantic_score > 0.82 and matched_unknown_terms > 0:
            score += 0.75

        scored_results.append((score, r))

    return apply_diversity_rerank(scored_results)
