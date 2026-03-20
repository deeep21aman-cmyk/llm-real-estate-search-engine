from RealtorDR.app.db import get_connection


def _vector_similarity_select(query_embedding):
    if query_embedding is None:
        return "0.0 AS vector_similarity", []

    return (
        """
        CASE
            WHEN p.description_embedding IS NULL THEN 0.0
            ELSE 1 - (p.description_embedding <=> %s::vector)
        END AS vector_similarity
        """,
        [query_embedding],
    )


def search_repo(bedrooms=None,
                bathrooms=None,
                min_bathrooms=None,
                max_bathrooms=None,
                min_bedrooms=None,
                max_bedrooms=None,
                min_price=None,
                max_price=None,
                min_size=None,
                max_size=None,
                min_lot_size=None,
                max_lot_size=None,
                min_year_built=None,
                max_year_built=None,
                is_discounted=None,

                # NEW DOWN PAYMENT FILTERS
                min_down_payment_amount=None,
                max_down_payment_amount=None,
                min_down_payment_percent=None,
                max_down_payment_percent=None,

                location=None,
                location_keywords=None,

                feature_names=None,
                keywords=None,
                query_embedding=None):

    conn = get_connection()
    conditions = []
    parameters = []
    match_score_parts = []
    match_score_params = []

    if feature_names is None:
        feature_names = []

    vector_similarity_sql, vector_params = _vector_similarity_select(query_embedding)

    base_query = f'''
    SELECT DISTINCT
        p.id,
        p.title,
        p.price,
        p.bedrooms,
        p.bathrooms,
        p.size,
        p.address,
        p.link,
        p.embedding_text,
        p.description_embedding,
        down_payment_amount,
        down_payment_percent,
        {{match_score}},
        {vector_similarity_sql}
    FROM properties p
    '''

    if (feature_names and len(feature_names) > 0) or keywords:
        base_query += '''
        LEFT JOIN property_features pf ON pf.property_id = p.id
        LEFT JOIN features f ON f.id = pf.feature_id
        '''

    # -------------------------------
    # BEDROOMS
    # -------------------------------

    if bedrooms is not None:
        conditions.append("p.bedrooms = %s")
        parameters.append(bedrooms)
        match_score_parts.append("CASE WHEN p.bedrooms = %s THEN 2 ELSE 0 END")
        match_score_params.append(bedrooms)

    if min_bedrooms is not None:
        conditions.append("p.bedrooms >= %s")
        parameters.append(min_bedrooms)
        match_score_parts.append("CASE WHEN p.bedrooms >= %s THEN 1 ELSE 0 END")
        match_score_params.append(min_bedrooms)

    if max_bedrooms is not None:
        conditions.append("p.bedrooms <= %s")
        parameters.append(max_bedrooms)
        match_score_parts.append("CASE WHEN p.bedrooms <= %s THEN 1 ELSE 0 END")
        match_score_params.append(max_bedrooms)

    # -------------------------------
    # BATHROOMS
    # -------------------------------

    if bathrooms is not None:
        conditions.append("p.bathrooms = %s")
        parameters.append(bathrooms)
        match_score_parts.append("CASE WHEN p.bathrooms = %s THEN 2 ELSE 0 END")
        match_score_params.append(bathrooms)

    if min_bathrooms is not None:
        conditions.append("p.bathrooms >= %s")
        parameters.append(min_bathrooms)
        match_score_parts.append("CASE WHEN p.bathrooms >= %s THEN 1 ELSE 0 END")
        match_score_params.append(min_bathrooms)

    if max_bathrooms is not None:
        conditions.append("p.bathrooms <= %s")
        parameters.append(max_bathrooms)
        match_score_parts.append("CASE WHEN p.bathrooms <= %s THEN 1 ELSE 0 END")
        match_score_params.append(max_bathrooms)

    # -------------------------------
    # PRICE
    # -------------------------------

    if min_price is not None:
        conditions.append("p.price >= %s")
        parameters.append(min_price)
        match_score_parts.append("CASE WHEN p.price >= %s THEN 2 ELSE 0 END")
        match_score_params.append(min_price)

    if max_price is not None:
        conditions.append("p.price <= %s")
        parameters.append(max_price)
        match_score_parts.append("CASE WHEN p.price <= %s THEN 2 ELSE 0 END")
        match_score_params.append(max_price)

    # -------------------------------
    # SIZE
    # -------------------------------

    if min_size is not None:
        conditions.append("p.size >= %s")
        parameters.append(min_size)
        match_score_parts.append("CASE WHEN p.size >= %s THEN 1 ELSE 0 END")
        match_score_params.append(min_size)

    if max_size is not None:
        conditions.append("p.size <= %s")
        parameters.append(max_size)
        match_score_parts.append("CASE WHEN p.size <= %s THEN 1 ELSE 0 END")
        match_score_params.append(max_size)

    # -------------------------------
    # LOT SIZE
    # -------------------------------

    if min_lot_size is not None:
        conditions.append("p.lot_size >= %s")
        parameters.append(min_lot_size)
        match_score_parts.append("CASE WHEN p.lot_size >= %s THEN 1 ELSE 0 END")
        match_score_params.append(min_lot_size)

    if max_lot_size is not None:
        conditions.append("p.lot_size <= %s")
        parameters.append(max_lot_size)
        match_score_parts.append("CASE WHEN p.lot_size <= %s THEN 1 ELSE 0 END")
        match_score_params.append(max_lot_size)

    # -------------------------------
    # YEAR BUILT
    # -------------------------------

    if min_year_built is not None:
        conditions.append("p.year_built >= %s")
        parameters.append(min_year_built)
        match_score_parts.append("CASE WHEN p.year_built >= %s THEN 1 ELSE 0 END")
        match_score_params.append(min_year_built)

    if max_year_built is not None:
        conditions.append("p.year_built <= %s")
        parameters.append(max_year_built)
        match_score_parts.append("CASE WHEN p.year_built <= %s THEN 1 ELSE 0 END")
        match_score_params.append(max_year_built)

    # -------------------------------
    # DISCOUNTED
    # -------------------------------

    if is_discounted is True:
        conditions.append("p.old_price IS NOT NULL AND p.old_price > p.price")

    # ---------------------------------------------------
    # DOWN PAYMENT FILTERS
    # Allow properties with matching values OR unknown
    # ---------------------------------------------------

    if min_down_payment_amount is not None:
        conditions.append(
            "(p.down_payment_amount IS NULL OR p.down_payment_amount >= %s)"
        )
        parameters.append(min_down_payment_amount)
        match_score_parts.append("CASE WHEN p.down_payment_amount >= %s THEN 2 ELSE 0 END")
        match_score_params.append(min_down_payment_amount)

    if max_down_payment_amount is not None:
        conditions.append(
            "(p.down_payment_amount IS NULL OR p.down_payment_amount <= %s)"
        )
        parameters.append(max_down_payment_amount)
        match_score_parts.append("CASE WHEN p.down_payment_amount <= %s THEN 2 ELSE 0 END")
        match_score_params.append(max_down_payment_amount)

    if min_down_payment_percent is not None:
        conditions.append(
            "(p.down_payment_percent IS NULL OR p.down_payment_percent >= %s)"
        )
        parameters.append(min_down_payment_percent)
        match_score_parts.append("CASE WHEN p.down_payment_percent >= %s THEN 2 ELSE 0 END")
        match_score_params.append(min_down_payment_percent)

    if max_down_payment_percent is not None:
        conditions.append(
            "(p.down_payment_percent IS NULL OR p.down_payment_percent <= %s)"
        )
        parameters.append(max_down_payment_percent)
        match_score_parts.append("CASE WHEN p.down_payment_percent <= %s THEN 2 ELSE 0 END")
        match_score_params.append(max_down_payment_percent)

    # ---------------------------------------------------
    # LOCATION FILTER
    # ---------------------------------------------------

    if location:
        conditions.append("LOWER(p.address) ILIKE %s")
        parameters.append(f"%{location.lower()}%")

    if location_keywords:
        for loc in location_keywords:
            match_score_parts.append(
                "CASE WHEN LOWER(p.address) ILIKE %s THEN 1 ELSE 0 END"
            )
            match_score_params.append(f"%{loc.lower()}%")

    # ---------------------------------------------------
    # FEATURE + KEYWORD SEARCH
    # ---------------------------------------------------

    or_conditions = []

    if feature_names and len(feature_names) > 0:
        for f in feature_names:
            or_conditions.append(
                "(LOWER(f.name) = %s OR LOWER(p.title) ILIKE %s)"
            )
            parameters.append(f.lower())
            parameters.append(f"%{f.lower()}%")
            match_score_parts.append(
                "CASE WHEN LOWER(f.name) = %s OR LOWER(p.title) ILIKE %s THEN 1 ELSE 0 END"
            )
            match_score_params.append(f.lower())
            match_score_params.append(f"%{f.lower()}%")

    if keywords:
        for word in keywords:
            or_conditions.append(
                "(LOWER(p.title) ILIKE %s OR LOWER(p.address) ILIKE %s)"
            )
            parameters.append(f"%{word.lower()}%")
            parameters.append(f"%{word.lower()}%")
            match_score_parts.append(
                "CASE WHEN LOWER(p.title) ILIKE %s OR LOWER(p.address) ILIKE %s THEN 1 ELSE 0 END"
            )
            match_score_params.append(f"%{word.lower()}%")
            match_score_params.append(f"%{word.lower()}%")

    if or_conditions:
        conditions.append("(" + " OR ".join(or_conditions) + ")")

    if match_score_parts:
        match_score_sql = " + ".join(match_score_parts)
    else:
        match_score_sql = "0"

    base_query = base_query.replace("{match_score}", f"({match_score_sql}) AS match_score")

    parameters = match_score_params + vector_params + parameters

    # -------------------------------
    # APPLY CONDITIONS
    # -------------------------------

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query = f"""
    SELECT *,
           (match_score + (vector_similarity * 0.5)) AS final_score
    FROM (
    {base_query}
    ) AS scored_properties
    ORDER BY final_score DESC
    LIMIT 20
    """

    print(base_query)
    #print(parameters)

    with conn:
        with conn.cursor() as cur:
            cur.execute(base_query, parameters)
            rows = cur.fetchall()

    conn.close()

    return rows


def vector_search_repo(query_embedding,
                       bedrooms=None,
                       bathrooms=None,
                       min_bathrooms=None,
                       max_bathrooms=None,
                       min_bedrooms=None,
                       max_bedrooms=None,
                       min_price=None,
                       max_price=None,
                       min_size=None,
                       max_size=None,
                       min_lot_size=None,
                       max_lot_size=None,
                       min_year_built=None,
                       max_year_built=None,
                       is_discounted=None):

    conn = get_connection()
    conditions = []
    parameters = []

    base_query = """
    SELECT
        p.id,
        p.title,
        p.price,
        p.bedrooms,
        p.bathrooms,
        p.size,
        p.address,
        p.link,
        p.embedding_text,
        p.description_embedding,
        down_payment_amount,
        down_payment_percent,
        0 AS match_score,
        CASE
            WHEN p.description_embedding IS NULL THEN 0.0
            ELSE 1 - (p.description_embedding <=> %s::vector)
        END AS vector_similarity
    FROM properties p
    """

    parameters.append(query_embedding)

    conditions.append("p.description_embedding IS NOT NULL")

    if bedrooms is not None:
        conditions.append("p.bedrooms = %s")
        parameters.append(bedrooms)

    if min_bedrooms is not None:
        conditions.append("p.bedrooms >= %s")
        parameters.append(min_bedrooms)

    if max_bedrooms is not None:
        conditions.append("p.bedrooms <= %s")
        parameters.append(max_bedrooms)

    if bathrooms is not None:
        conditions.append("p.bathrooms = %s")
        parameters.append(bathrooms)

    if min_bathrooms is not None:
        conditions.append("p.bathrooms >= %s")
        parameters.append(min_bathrooms)

    if max_bathrooms is not None:
        conditions.append("p.bathrooms <= %s")
        parameters.append(max_bathrooms)

    if min_price is not None:
        conditions.append("p.price >= %s")
        parameters.append(min_price)

    if max_price is not None:
        conditions.append("p.price <= %s")
        parameters.append(max_price)

    if min_size is not None:
        conditions.append("p.size >= %s")
        parameters.append(min_size)

    if max_size is not None:
        conditions.append("p.size <= %s")
        parameters.append(max_size)

    if min_lot_size is not None:
        conditions.append("p.lot_size >= %s")
        parameters.append(min_lot_size)

    if max_lot_size is not None:
        conditions.append("p.lot_size <= %s")
        parameters.append(max_lot_size)

    if min_year_built is not None:
        conditions.append("p.year_built >= %s")
        parameters.append(min_year_built)

    if max_year_built is not None:
        conditions.append("p.year_built <= %s")
        parameters.append(max_year_built)

    if is_discounted is True:
        conditions.append("p.old_price IS NOT NULL AND p.old_price > p.price")

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += """
    ORDER BY p.description_embedding <-> %s::vector
    LIMIT 10
    """

    parameters.append(query_embedding)

    with conn:
        with conn.cursor() as cur:
            cur.execute(base_query, parameters)
            rows = cur.fetchall()

    conn.close()

    return rows
