def normalize_keywords(unknown_terms):

    keywords = []

    for term in unknown_terms:
        words = term.lower().split()

        for word in words:
            word = word.strip()

            if len(word) > 2:
                keywords.append(word)

    return list(set(keywords))