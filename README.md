# AI Real Estate Search Engine

An AI-powered real estate search engine capable of understanding natural language queries and returning relevant property listings using a hybrid search architecture.

Example query:

"luxury property with helipad in Punta Cana under 900k"

The system converts natural language queries into structured filters and semantic search signals, then ranks properties based on relevance.

---

## Key Features

### Natural Language Query Understanding
Uses an LLM-based intent parser to convert user queries into structured filters such as:

- bedrooms
- bathrooms
- price range
- property size
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

### Hybrid Search Architecture
The search engine combines multiple retrieval techniques:

• Structured SQL filtering (PostgreSQL)
• Semantic vector similarity search (pgvector)
• Keyword matching in titles and descriptions

This hybrid architecture provides both precision and semantic understanding.

---

### Intelligent Ranking Engine
Results are ranked using a scoring system that considers:

- structured attribute matches
- semantic similarity to the query
- feature matches
- location matches
- keyword relevance

This ensures relevant results even when queries are vague.

---

### Constraint Relaxation
If no exact matches are found, the system automatically relaxes constraints and returns the closest relevant properties.

Example:

User query:

"20 bedroom house under 200k"

System response:

"We couldn't find an exact match, but here are similar properties you may be interested in."

---

### Result Explanation Engine
Each property result includes an explanation describing why it matched the query.

Example:

```
✓ Property has 4 bedrooms as requested
✓ Property is located in Punta Cana
✓ Property matches your search for luxury
✗ Property does not have solar panels
```

This improves transparency and helps users understand the results.

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
- NumPy
- Natural Language Processing (NLP)

---

## Project Structure

```
app/
 ├── main_pipeline.py
 ├── intent_parser.py
 ├── query_processing.py
 ├── search_repository.py
 ├── ranking_engine.py
 ├── explanation_engine.py
 ├── result_display.py
 ├── embeddings.py
 ├── generate_embeddings.py
 ├── downpayment_calc.py
 └── config.py

 data/
 ├── all_properties.json
 └── oneproperty.json

 README.md
 requirements.txt
```

---

## System Architecture

Pipeline Overview:

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

## Running the Project

### 1. Clone the repository

```
git clone https://github.com/yourusername/ai-real-estate-search-engine.git
cd ai-real-estate-search-engine
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file with:

```
OPENAI_API_KEY=your_api_key_here
```

### 4. Run the API server

```
uvicorn app.api:app --reload
```

The backend exposes a single endpoint:

```
POST /chat
```

Example request:

```
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"4 bedroom luxury property in Punta Cana with pool"}'
```

---

## Future Improvements

Potential enhancements include:

- synonym expansion (e.g., helipad ↔ heliport)
- faster ranking using approximate nearest neighbors
- caching layer for frequent queries
- web interface or REST API
- geospatial search for better location matching

---

## Author

Amandeep Kaur
