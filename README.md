

# AI Real Estate Search Engine

An AI-powered real estate search engine capable of understanding natural language queries and returning relevant property listings using a hybrid search architecture.

Example query:

"luxury property with helipad in Punta Cana under 900k"

The system converts the natural language query into structured filters and semantic search signals, then ranks properties based on relevance.

---

## Key Features

### 1. Natural Language Query Understanding
Uses an LLM-based intent parser to convert user queries into structured filters such as:

- bedrooms
- bathrooms
- price range
- size
- lot size
- year built
- property features
- location
- down payment requirements

Example parsed output:

```
{
  "min_bedrooms": 3,
  "max_price": 900000,
  "feature_names": ["helipad"],
  "location": "punta cana"
}
```

---

### 2. Hybrid Search Architecture
The search engine combines multiple retrieval techniques:

• Structured SQL filtering (PostgreSQL)
• Semantic vector similarity search (pgvector)
• Keyword matching in property titles and descriptions

This hybrid approach ensures both precise filtering and semantic understanding of user intent.

---

### 3. Intelligent Ranking Engine
Results are ranked using a scoring system that considers:

- structured field matches (bedrooms, price, etc.)
- semantic similarity to the query
- feature matches
- location matches
- keyword relevance

This produces highly relevant results even when queries are ambiguous.

---

### 4. Constraint Relaxation
If no exact matches are found, the system automatically relaxes constraints and returns the closest relevant properties.

Example:

User query:

"20 bedroom house under 200k"

System response:

"We couldn't find an exact match, but here are similar properties you may be interested in."

---

### 5. Result Explanation Engine
Each result includes an explanation describing why it matched the user's query.

Example:

```
✓ Property has 4 bedrooms as requested
✓ Property is located in Punta Cana
✓ Property matches your search for luxury
✗ Property does not have solar panels
```

This improves transparency and helps users understand how results were selected.

---

## Example Query

```
What properties are you interested in?
> luxury villa with helipad in Punta Cana
```

Example output:

```
Title: Expansive Luxury Villa With Helipad
Price: $2,900,000
Location: Punta Cana

✓ Property has a helipad
✓ Property matches your search for luxury
✓ Property located in Punta Cana
```

---

## Tech Stack

- Python
- PostgreSQL
- pgvector
- OpenAI API
- Natural Language Processing (NLP)
- Semantic Search

---

## System Architecture

Pipeline overview:

User Query
↓
Intent Parser (LLM)
↓
Query Processing
↓
Structured Search (SQL)
↓
Vector Similarity Search
↓
Ranking Engine
↓
Explanation Engine
↓
Final Results

---

## Future Improvements

Potential enhancements include:

- synonym expansion (e.g., helipad ↔ heliport)
- faster ranking using approximate nearest neighbors
- caching layer for popular queries
- web interface or API endpoint
- geospatial location search

---

## Author

Amandeep Kaur