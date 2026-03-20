from app.explanation_engine import generate_explanation


def format_property(parsed, keywords, row, result_type):
    """
    Convert a database row into a structured property result.
    """

    title = row[1]
    price = row[2]
    bedrooms = row[3]
    bathrooms = row[4]
    size = row[5]
    address = row[6]
    link = row[7]

    reasons = generate_explanation(parsed, keywords, row, result_type)

    explanation = ""
    if reasons:
        explanation = "\n".join(reasons)

    return {
        "title": title,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "size": size,
        "address": address,
        "link": link,
        "explanation": explanation,
    }


def format_results(parsed, keywords, top_results, additional, sections=None):
    """
    Convert pipeline results into API-friendly output format.

    Supports two modes:
    1) Legacy mode using top_results + additional_results
    2) Sectioned mode using categorized result groups
    """

    # -----------------------
    # Legacy mode (existing behavior)
    # -----------------------
    if sections is None:

        formatted_top = []
        formatted_additional = []

        for r in top_results:
            formatted_top.append(format_property(parsed, keywords, r, "top"))

        for r in additional:
            formatted_additional.append(format_property(parsed, keywords, r, "additional"))

        return {
            "top_results": formatted_top,
            "additional_results": formatted_additional,
        }

    # -----------------------
    # Sectioned results mode
    # -----------------------
    formatted_sections = {}

    for section_name, rows in sections.items():

        formatted_rows = []

        for r in rows:
            formatted_rows.append(
                format_property(parsed, keywords, r, section_name)
            )

        formatted_sections[section_name] = formatted_rows

    # Also build flattened lists for backward compatibility
    flattened = []
    for rows in formatted_sections.values():
        flattened.extend(rows)

    top = flattened[:6]
    additional = flattened[6:]

    return { 
        "sections": formatted_sections,
        "top_results": top,
        "additional_results": additional
    }
