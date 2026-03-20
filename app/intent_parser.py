from RealtorDR.app.db import get_connection
from openai import OpenAI
import os
from RealtorDR.app.config import OPEN_AI_MODEL
import json
from functools import lru_cache

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("set API KEY")

client=OpenAI(api_key=OPENAI_API_KEY)

@lru_cache(maxsize=1)
def get_cached_feature_names():
    conn=get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM features WHERE count>0 ORDER BY name")
        db_feature_names=tuple(cur.fetchall())
    conn.close()
    return db_feature_names

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
    db_feature_names=list(get_cached_feature_names())
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

LOCATION RULES

Location refers ONLY to geographic place names such as:

• cities
• neighborhoods
• regions
• districts
• well-known real estate areas

Examples of valid locations:

punta cana
cap cana
sosua
cabarete
bavaro
puerto plata
santo domingo

These should populate the "location" field.

Example:
"villa in Punta Cana"
→ location = "punta cana"

Do NOT treat environmental or descriptive terms as locations.

The following are NOT locations:

beach
ocean
ocean view
beachfront
airport
marina
golf course
park
shopping area
near beach
close to ocean

These must NOT populate the "location" field.

Instead:
• If they represent a property feature → map to feature_names
• Otherwise place them in unknown_terms

location_keywords should only contain additional geographic words that help identify a place (for example "bavaro", "cap", "cana").

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
investment
near beach
close to ocean
walking distance to beach

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

# ===== INTENT CLASSIFIER =====
def detect_intent(user_query: str) -> str:
    prompt = """
Classify the user query into ONE category:

1. PROPERTY_SEARCH → the user wants to find, browse, or get property listings
2. KNOWLEDGE_SEARCH → the user is asking a question or seeking information

Guidelines:

- Choose PROPERTY_SEARCH if the user is describing a property they want:
  (examples: bedrooms, price, location, features, type of property)

- Choose PROPERTY_SEARCH if the user is trying to see options or listings, even if they mention goals like investment

- Choose KNOWLEDGE_SEARCH if the user is asking for explanations, advice, or general information

- If the query includes both (e.g., property + question), prioritize PROPERTY_SEARCH

Examples:

"3 bedroom condo in Punta Cana"
→ PROPERTY_SEARCH

"villa with pool under 300k"
→ PROPERTY_SEARCH

"3 bedroom investment property in Punta Cana"
→ PROPERTY_SEARCH

"is it a good investment?"
→ KNOWLEDGE_SEARCH

"how does financing work?"
→ KNOWLEDGE_SEARCH

"what areas are best for families?"
→ KNOWLEDGE_SEARCH

"show me beachfront condos"
→ PROPERTY_SEARCH

Query:
{{ $json.message }}

Answer ONLY one word:
PROPERTY_SEARCH or KNOWLEDGE_SEARCH
"""

    response = client.responses.create(
        model=OPEN_AI_MODEL,
        temperature=0,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": prompt}]
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_query}]
            }
        ]
    )

    intent = response.output_text.strip().upper()

    if intent not in ["PROPERTY_SEARCH", "KNOWLEDGE_SEARCH"]:
        return "PROPERTY_SEARCH"

    return intent
