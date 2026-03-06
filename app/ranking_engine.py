import numpy as np
import ast

def cosine_similarity(a, b):

    a = np.array(a)
    b = np.array(ast.literal_eval(b))

    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def rank_results(search_results, query_embedding):

    scored_results = []

    for r in search_results:

        property_embedding = r[9]
        match_score = r[12]

        semantic_score = cosine_similarity(query_embedding, property_embedding)

        score = semantic_score

        if match_score > 0:
            score += match_score * 1.2

        if match_score >= 1:
            score += 1.0

        scored_results.append((score, r))

    scored_results.sort(reverse=True, key=lambda x: x[0])

    return scored_results