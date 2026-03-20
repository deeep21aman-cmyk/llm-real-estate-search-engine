from RealtorDR.app.explanation_engine import generate_explanation


def display_property(parsed, keywords, r, reason_header, result_type):

    title = r[1]
    price = r[2]
    bedrooms = r[3]
    bathrooms = r[4]
    size = r[5]
    address = r[6]
    link = r[7]

    print("-------------------------------------")
    print(f"Title: {title}")
    print(f"Price: ${price}")
    print(f"Bedrooms: {bedrooms}")
    print(f"Bathrooms: {bathrooms}")
    print(f"Size: {size} sqm")
    print(f"Address: {address}")
    print(f"Link: {link}\n")

    reasons = generate_explanation(parsed, keywords, r, result_type)

    if reasons:
        print(reason_header)

        for reason in reasons:
            print(reason)

    print()


def display_results(parsed, keywords, top_results, additional):

    if top_results:

        print("\nTop matching results:\n")

        for r in top_results:
            display_property(parsed, keywords, r, "Why this property matched:", "top")

        if additional:

            print("\nOther similar properties you may be interested in:\n")

            for r in additional:
                display_property(parsed, keywords, r, "Why this property might interest you:", "additional")

    else:

        print("\nWe couldn't find an exact match for your search.")
        print("But here are some other properties you may be interested in:\n")

        for r in additional:
            display_property(parsed, keywords, r, "Why this property might interest you:", "additional")
