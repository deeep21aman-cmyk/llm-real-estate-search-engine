import os
from openai import OpenAI
from db import get_connection
from config import EMBEDDING_MODEL,OPEN_AI_MODEL

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("set API KEY")

client=OpenAI(api_key=OPENAI_API_KEY)


ATTRIBUTE_PROMPT = """
You are preparing structured text for semantic search embeddings for a real estate database.

Your goal is to preserve ALL useful information about a property so it can be found through search queries.

DO NOT remove information unless it is completely meaningless.

Even promotional text should generally be preserved because it may contain useful context.

The goal is NOT summarization.
The goal is structured attribute extraction while keeping every meaningful detail.

--------------------------------------------------

IMPORTANT RULES

1. Preserve ALL information related to the property.
2. Do NOT shorten financial information or payment plans.
3. Preserve all numbers exactly.
4. Preserve percentages and dollar amounts.
5. Preserve reservation deposits, down payments, installment schedules, and financing terms.
6. Preserve the full payment plan structure in the same order it appears.

--------------------------------------------------

NORMALIZATION RULES

If shorthand monetary values appear, convert them to full USD format.

Examples:
5k → $5000
10k → $10000
1.5k → $1500

Always use the format:
$NUMBER

Examples:
$5000
$15000
$250000

--------------------------------------------------

PROPERTY INFORMATION TO PRESERVE

Include all of the following if present:

Property characteristics
- property type
- bedrooms
- bathrooms
- interior size
- lot size
- year built
- floors
- levels

Property features
- pool
- solar panels
- balcony
- terrace
- garage
- parking
- garden
- elevator
- security
- gated community
- furnished
- smart home features
- appliances
- water systems
- generators
- solar systems

Views and environment
- ocean view
- mountain view
- garden view
- beachfront
- hillside
- city view

Location information
- city
- neighborhood
- country
- distances to beach
- distances to airport
- distances to town

Examples:
5 minutes to beach
10 minutes to airport

--------------------------------------------------

FINANCING AND PURCHASE TERMS

Preserve ALL financial structures.

This includes:

- payment plans
- installment plans
- reservation deposits
- promise of sale payments
- construction payments
- developer financing
- seller financing
- interest rates
- loan terms
- financing percentages
- financing duration

Examples of structures to preserve:

payment plan: $5000 reservation, 20%, 40%, 40%

down payment: 20%

down payment amount: $5000 + 20%

payment plan: $5000, 20%, 25%, 25%, 25%, 5%

reservation deposit $5000, 30% upon signing promise of sale

financing available, 7% interest, 5 year term

developer financing up to 30%

--------------------------------------------------

CRITICAL PAYMENT PLAN RULE

If payment plan information exists:

Preserve BOTH the deposit AND the installment schedule.

Examples of correct format:

down payment: 20%
payment plan: 20%, 30%, 50%

down payment amount: $5000
payment plan: $5000, 20%, 40%, 40%

down payment amount: $5000 + 20%
payment plan: $5000, 20%, 25%, 25%, 25%, 5%

reservation deposit: $5000
payment plan: $5000, 30%, 20%, 20%, 20%, 10%

Do NOT calculate anything.
Do NOT remove steps from the payment schedule.

Always preserve the full structure.

--------------------------------------------------

OUTPUT FORMAT

Return a comma-separated list of attributes.

Do NOT write sentences.
Do NOT add explanations.
Do NOT invent information.

Example output:

luxury beachfront villa, 4 bedrooms, 3 bathrooms,
320 sqm interior, 900 sqm lot,
private pool, solar panels, rooftop terrace,
gated community, ocean view,
5 minutes to beach, 10 minutes to airport,
investment opportunity,
reservation deposit $5000,
down payment: 20%,
payment plan: $5000, 20%, 30%, 30%, 20%
"""

def get_embedding(text):
    response=client.embeddings.create(model=EMBEDDING_MODEL,input=text)
    return response.data[0].embedding

def cleanup_text(raw_text):
    
    response = client.responses.create(
        model=OPEN_AI_MODEL,
        temperature=0,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": ATTRIBUTE_PROMPT}]},
            {"role": "user", "content": [{"type": "input_text", "text": raw_text}]}
        ]
    )

    return response.output_text.strip()


def generate_embeddings():
    conn=get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute('''
SELECT 
id,
title,
description,
address,
bedrooms,
bathrooms,
size,
lot_size,
year_built
FROM properties
WHERE embedding_text IS NULL
                ''')
            rows=cur.fetchall()
                        
    
            for row in rows:
                property_id=row[0]
                title=row[1]
                description=row[2]
                address=row[3]
                bedrooms=row[4]
                bathrooms=row[5]
                size=row[6]
                lot_size=row[7]
                year_built=row[8]
                cur.execute("""
SELECT f.name
FROM property_features pf
JOIN features f ON f.id = pf.feature_id
WHERE pf.property_id = %s
""", (property_id,))
                features = [f[0] for f in cur.fetchall()]
                features_text = ", ".join(features)
                raw_text =  f"""
Title: {title}

Address: {address}

Bedrooms: {bedrooms}
Bathrooms: {bathrooms}
Size: {size}
Lot Size: {lot_size}
Year Built: {year_built}

Features: {features_text}

Description:
{description}
"""
                cleaned_text=cleanup_text(raw_text)
                cur.execute(
    "UPDATE properties SET embedding_text=%s WHERE id=%s",
    (cleaned_text, property_id)
)
                #embedding=get_embedding(cleaned_text)
               #cur.execute("UPDATE properties SET description_embedding=%s WHERE  id=%s",(embedding,property_id))
            
    conn.close()

generate_embeddings()