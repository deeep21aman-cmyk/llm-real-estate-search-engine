def normalize_keywords(unknown_terms):

    keywords = []

    for term in unknown_terms:

        cleaned = term.lower().strip()

        # ignore very small meaningless terms
        if len(cleaned) <= 2:
            continue

        keywords.append(cleaned)

    # remove duplicates while preserving phrases
    return list(set(keywords))