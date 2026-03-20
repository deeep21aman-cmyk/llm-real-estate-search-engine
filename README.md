# 🏡 RealtorDR — AI-Powered Real Estate Search Engine

RealtorDR is an AI-powered real estate search system that lets users query property listings using natural language instead of rigid filters.

It combines **LLM-based intent parsing**, **structured database filtering**, and **semantic vector search** to deliver highly relevant results.

---

## 🚀 Features

- 🔍 Natural language search  
  _Example: “3 bedroom house under 800k near downtown with garage”_

- 🧠 AI intent parsing → converts text into structured filters
- ⚡ Hybrid search:
  - Structured filtering (price, beds, baths, location)
  - Semantic search (embeddings + vector similarity)
- 🏆 Custom ranking engine for best-match results
- 💬 Explanation engine for transparent results
- 📊 Down payment calculator support

---

## 🧠 System Architecture

```
User Query
   ↓
Intent Parser (LLM)
   ↓
Query Processing / Normalization
   ↓
Hybrid Search:
   ├── Structured DB Query
   └── Vector Similarity Search
   ↓
Ranking Engine
   ↓
Results Formatter + Explanation Engine
   ↓
Final Output
```

---

## 📂 Project Structure

```
RealtorDR/
├── app/
│   ├── api.py
│   ├── config.py
│   ├── db.py
│   ├── embeddings.py
│   ├── intent_parser.py
│   ├── query_processing.py
│   ├── search_repository.py
│   ├── ranking_engine.py
│   ├── results_formatter.py
│   ├── explanation_engine.py
│   ├── main_pipeline.py
│   └── ...
├── data/
│   ├── all_properties.json
│   └── oneproperty.json
├── requirements.txt
└── .env
```

---

## ⚙️ Setup

### 1. Clone the repo
```
git clone <your-repo-url>
cd RealtorDR
```

### 2. Create virtual environment
```
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```
OPENAI_API_KEY=your_key_here
DATABASE_URL=your_db_url
```

---

## ▶️ Run the System

### Option 1: Run pipeline directly
```
python -m app.main_pipeline
```

### Option 2: Run API server
```
uvicorn app.api:app --reload
```

Endpoint:
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

## 🧪 Example Query

```
"2 bedroom condo under 600k with parking in Toronto"
```

### Output includes:
- Ranked property results
- Match explanations
- Structured attributes

---

## 🛠 Tech Stack

- Python
- OpenAI (LLM + embeddings)
- PostgreSQL
- pgvector
- NumPy

---

## 🎯 Key Design Principles

- Hybrid search > keyword-only search  
- Explainable results (not black-box AI)  
- Modular architecture for scalability  
- Fast iteration over perfect abstraction  

---

## 🚧 Future Improvements

- Real-time MLS integration  
- Caching layer for faster queries  
- Advanced ranking signals (user preferences)  
- UI layer (web/mobile)  

---

## 👤 Author

Amandeep Kaur
