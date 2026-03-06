from db import get_connection
from openai import OpenAI
import os
from config import OPEN_AI_MODEL
import json

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("set API KEY")

client=OpenAI(api_key=OPENAI_API_KEY)
def validate_llm_output(db_feature_names, output_dict):

    expected_keys = {
        "bedrooms",
        "min_bedrooms",
        "max_bedrooms",
        "min_bathrooms",
        "max_bathrooms",
        "bathrooms",
        "min_price",
        "max_price",
        "min_size",
        "max_size",
        "min_lot_size",
        "max_lot_size",
        "min_year_built",
        "max_year_built",
        "is_discounted",

        # NEW DOWN PAYMENT FIELDS
        "min_down_payment_amount",
        "max_down_payment_amount",
        "min_down_payment_percent",
        "max_down_payment_percent",

        "location",
        "location_keywords",

        "feature_names",
        "unknown_terms"
    }

    output_keys = set(output_dict.keys())

    if output_keys != expected_keys:
        raise ValueError("Json output doesnt match expected format")


    # ---------------------------
    # INTEGER FIELDS
    # ---------------------------

    integer_fields = [
        "bedrooms",
        "min_bedrooms",
        "max_bedrooms",
        "min_bathrooms",
        "max_bathrooms",
        "bathrooms",
        "min_year_built",
        "max_year_built"
    ]

    for field in integer_fields:
        value = output_dict[field]
        if value is not None and not isinstance(value, int):
            raise ValueError(f"{field} must be an integer or null")


    # ---------------------------
    # NUMERIC FIELDS
    # ---------------------------

    int_float_fields = [
        "min_price",
        "max_price",
        "min_size",
        "max_size",
        "min_lot_size",
        "max_lot_size",

        # NEW DOWN PAYMENT NUMERIC FIELDS
        "min_down_payment_amount",
        "max_down_payment_amount",
        "min_down_payment_percent",
        "max_down_payment_percent"
    ]

    for field in int_float_fields:
        value = output_dict[field]
        if value is not None and not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be an integer or float or null")


    # ---------------------------
    # BEDROOM RULES
    # ---------------------------

    if output_dict["bedrooms"] is not None:
        if output_dict["min_bedrooms"] is not None or output_dict["max_bedrooms"] is not None:
            raise ValueError("Cannot set bedrooms together with min_bedrooms or max_bedrooms")

    if output_dict["min_bedrooms"] is not None and output_dict["max_bedrooms"] is not None:
        if output_dict["min_bedrooms"] > output_dict["max_bedrooms"]:
            raise ValueError("min_bedrooms cannot be greater than max_bedrooms")


    # ---------------------------
    # BATHROOM RULES
    # ---------------------------

    if output_dict["bathrooms"] is not None:
        if output_dict["min_bathrooms"] is not None or output_dict["max_bathrooms"] is not None:
            raise ValueError("Cannot set bathrooms together with min_bathrooms or max_bathrooms")

    if output_dict["min_bathrooms"] is not None and output_dict["max_bathrooms"] is not None:
        if output_dict["min_bathrooms"] > output_dict["max_bathrooms"]:
            raise ValueError("min_bathrooms cannot be greater than max_bathrooms")


    # ---------------------------
    # DOWN PAYMENT VALIDATION
    # ---------------------------

    if output_dict["min_down_payment_amount"] is not None and output_dict["max_down_payment_amount"] is not None:
        if output_dict["min_down_payment_amount"] > output_dict["max_down_payment_amount"]:
            raise ValueError("min_down_payment_amount cannot be greater than max_down_payment_amount")

    if output_dict["min_down_payment_percent"] is not None and output_dict["max_down_payment_percent"] is not None:
        if output_dict["min_down_payment_percent"] > output_dict["max_down_payment_percent"]:
            raise ValueError("min_down_payment_percent cannot be greater than max_down_payment_percent")


    # ---------------------------
    # BOOLEAN VALIDATION
    # ---------------------------

    if output_dict["is_discounted"] is not None and not isinstance(output_dict["is_discounted"], bool):
        raise ValueError("is_discounted must be a boolean or null")


    # ---------------------------
    # LOCATION VALIDATION
    # ---------------------------

    if output_dict["location"] is not None and not isinstance(output_dict["location"], str):
        raise ValueError("location must be a string or null")

    if not isinstance(output_dict["location_keywords"], list):
        raise ValueError("location_keywords must be a list")

    for loc in output_dict["location_keywords"]:
        if not isinstance(loc, str):
            raise ValueError("location_keywords entries must be strings")


    # ---------------------------
    # UNKNOWN TERMS
    # ---------------------------

    if not isinstance(output_dict["unknown_terms"], list):
        raise ValueError("unknown_terms must be a list")

    for term in output_dict["unknown_terms"]:
        if not isinstance(term, str):
            raise ValueError(f"{term} must be a string")


    # ---------------------------
    # FEATURE NAMES
    # ---------------------------

    if not isinstance(output_dict["feature_names"], list):
        raise ValueError("feature_names must be a list")

    for feature in output_dict["feature_names"]:
        if feature is None or not isinstance(feature, str):
            raise ValueError(f"{feature} must be a string")


    # ---------------------------
    # CLEAN UNKNOWN TERMS
    # ---------------------------

    cleaned_unknown = []
    seen_unknown = set()

    for feature in output_dict["unknown_terms"]:
        cleaned = feature.strip().lower()
        if cleaned not in seen_unknown:
            seen_unknown.add(cleaned)
            cleaned_unknown.append(cleaned)

    output_dict["unknown_terms"] = cleaned_unknown


    # ---------------------------
    # CLEAN FEATURE NAMES
    # ---------------------------

    cleaned_features = []
    seen_features = set()

    for feature in output_dict["feature_names"]:
        cleaned = feature.strip().lower()
        if cleaned not in seen_features:
            seen_features.add(cleaned)
            cleaned_features.append(cleaned)

    output_dict["feature_names"] = cleaned_features


    # ---------------------------
    # FEATURE VALIDATION
    # ---------------------------

    valid_features = {row[0].lower() for row in db_feature_names}

    for feature in output_dict["feature_names"]:
        if feature not in valid_features:
            raise ValueError(f"{feature} not in valid feature list")


    return output_dict

def parse_user_query(user_query: str):
    conn=get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM features WHERE count>0 ORDER BY name")
        db_feature_names=cur.fetchall()
    conn.close()
    features = '\n'.join(row[0] for row in db_feature_names)
    feature_list_text = features

    system_prompt = f'''
You are a real estate search query parser.

Your task is to convert a user message into structured filters.

You must return ONLY a valid JSON object.
Do not include explanations.
Do not include markdown.
Do not include text before or after the JSON.
Do not wrap the JSON in code blocks.

OUTPUT SCHEMA

Return exactly the following JSON structure:

{{
"bedrooms": integer or null,
"min_bedrooms": integer or null,
"max_bedrooms": integer or null,

"bathrooms": integer or null,
"min_bathrooms": integer or null,
"max_bathrooms": integer or null,

"min_price": number or null,
"max_price": number or null,

"min_size": number or null,
"max_size": number or null,

"min_lot_size": number or null,
"max_lot_size": number or null,

"min_year_built": integer or null,
"max_year_built": integer or null,

"is_discounted": boolean or null,

"min_down_payment_amount": number or null,
"max_down_payment_amount": number or null,

"min_down_payment_percent": number or null,
"max_down_payment_percent": number or null,

"location": string or null,
"location_keywords": array of strings,

"feature_names": array of strings,
"unknown_terms": array of strings
}}

GENERAL RULES
• If a filter is not mentioned, return null.
• feature_names must always be an array (empty array if none).
• unknown_terms must always be an array (empty array if none).
• Do not create additional keys.
• Return valid JSON only.
• Down payment expressions must populate the down payment fields and must NOT appear in unknown_terms.

--------------------------------------------------

GENERIC PROPERTY WORDS

Users often include generic words that simply describe the type of thing being searched.

These words are NOT meaningful search attributes and must NOT appear in unknown_terms.

Ignore these words completely:

house
home
property
properties
real estate
listing
place
residence
unit

Example:

User query:
"luxury house with pool"

Correct output:
feature_names = ["pool"]
unknown_terms = ["luxury"]

NOT:
unknown_terms = ["luxury","house"]

--------------------------------------------------

STRUCTURAL WORDS

Words that refer to structured filters must NEVER appear in unknown_terms.

These include:

bedroom
bedrooms
bathroom
bathrooms
price
size
lot
square feet
sqft
year built
down payment
deposit

These concepts must populate the correct structured fields instead.

--------------------------------------------------

BEDROOM RULES

Exact value:
"3 bedrooms", "exactly 3 bedrooms" → bedrooms = 3

Minimum:
"3+ bedrooms", "at least 3 bedrooms", "minimum 3 bedrooms" → min_bedrooms = 3

Maximum:
"up to 4 bedrooms", "no more than 4 bedrooms", "max 4 bedrooms" → max_bedrooms = 4

Range:
"between 2 and 4 bedrooms" → min_bedrooms = 2 and max_bedrooms = 4

If bedrooms is set, min_bedrooms and max_bedrooms must be null.

--------------------------------------------------

BATHROOM RULES

Apply the same logic as bedrooms for bathrooms.

--------------------------------------------------

PRICE RULES

"over 500k", "above 500k", "at least 500k" → min_price  
"under 800k", "below 800k", "max 800k" → max_price  
"between 400k and 600k" → min_price and max_price

--------------------------------------------------

SIZE RULES

Interior size mentions (sqft, square feet) → min_size or max_size

Lot or land size mentions → min_lot_size or max_lot_size

Apply the same comparison logic as price.

--------------------------------------------------

YEAR BUILT RULES

"built after 2015" → min_year_built = 2016  
"built before 2000" → max_year_built = 1999  
"built between 2000 and 2010" → min_year_built and max_year_built

--------------------------------------------------

DISCOUNT RULE

If the query mentions discounts, deals, price reductions, or reduced price  
→ is_discounted = true

--------------------------------------------------

DOWN PAYMENT RULES

Users may search for properties based on required down payment.

Extract these values into the correct fields.

DOWN PAYMENT PERCENT

"20% down payment"
→ min_down_payment_percent = 20
→ max_down_payment_percent = 20

"10% down homes"
→ min_down_payment_percent = 10
→ max_down_payment_percent = 10

"low down payment homes"
→ max_down_payment_percent = 10

"under 20% down payment"
→ max_down_payment_percent = 20

"at least 25% down payment"
→ min_down_payment_percent = 25

DOWN PAYMENT AMOUNT

"$5,000 down payment"
→ min_down_payment_amount = 5000
→ max_down_payment_amount = 5000

"properties requiring $50k down"
→ min_down_payment_amount = 50000
→ max_down_payment_amount = 50000

"down payment under $20k"
→ max_down_payment_amount = 20000

"down payment above $100k"
→ min_down_payment_amount = 100000

If both percent and amount are mentioned, populate both fields.

Examples:

"$5k deposit and 10% down"
→ min_down_payment_amount = 5000
→ min_down_payment_percent = 10

--------------------------------------------------

VALID FEATURE LIST

The following features are the canonical feature vocabulary.
Only these values may appear in "feature_names".

Normalize all features to lowercase.

{feature_list_text}

--------------------------------------------------

FEATURE MATCHING RULES

Users may describe property features using different wording.

You must interpret the meaning of the user text and map it to the
closest feature from the VALID FEATURE LIST.

Examples:

User: "solar powered house"  
Feature list contains: "solar panels"  
→ feature_names = ["solar panels"]

User: "house with a swimming pool"  
Feature list contains: "pool"  
→ feature_names = ["pool"]

User: "electric car charger"  
Feature list contains: "ev charging"  
→ feature_names = ["ev charging"]

Always output the feature exactly as written in the VALID FEATURE LIST.

--------------------------------------------------

UNKNOWN TERMS RULE

If a user mentions a descriptive or semantic concept that:

• is not a structured filter  
• is not a feature from the VALID FEATURE LIST  
• is not a generic property word

then it must be placed in "unknown_terms".

Examples:

luxury  
modern  
investment property  
ocean view  
near beach  

Down payment phrases must NOT appear in unknown_terms.

--------------------------------------------------

Example Output

{{
"bedrooms": null,
"min_bedrooms": null,
"max_bedrooms": null,
"bathrooms": null,
"min_bathrooms": null,
"max_bathrooms": null,
"min_price": null,
"max_price": null,
"min_size": null,
"max_size": null,
"min_lot_size": null,
"max_lot_size": null,
"min_year_built": null,
"max_year_built": null,
"is_discounted": null,
"min_down_payment_amount": null,
"max_down_payment_amount": null,
"min_down_payment_percent": null,
"max_down_payment_percent": null,
"location": null,
"location_keywords": [],
"feature_names": [],
"unknown_terms": []
}}
'''
    response = client.responses.create(model=OPEN_AI_MODEL,temperature=0,
    input=[
        {
            "role": "system",
            "content": [
                {"type": "input_text", "text": system_prompt}
            ]
        },
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_query}
            ]
        }
    ]
        )
    try:
        output_dict=json.loads(response.output_text)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}")
    

    return validate_llm_output(db_feature_names,output_dict)