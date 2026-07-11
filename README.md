# AI Document Intelligence

A Retrieval-Augmented Generation (RAG) system that lets you upload a PDF, ask natural-language questions about it, and get answers grounded strictly in the document — with page-level source citations and a built-in "I don't know" fallback for out-of-scope questions.

## Features
- Upload any text-based PDF
- Automatic text extraction (pypdf)
- Chunking with overlap for context preservation
- Local embeddings (SentenceTransformers `all-MiniLM-L6-v2`)
- Persistent vector storage (ChromaDB)
- Question answering via Groq (`llama-3.3-70b-versatile`)
- Page-number source attribution on every answer
- Strict hallucination guardrail ("I don't know" when answer isn't in the document)
- Console logging across the full pipeline
- Simple built-in HTML UI (no separate frontend needed)

## Tech Stack
| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| PDF Parsing | pypdf |
| Embeddings | SentenceTransformers (local, `all-MiniLM-L6-v2`) |
| Vector Store | ChromaDB (persistent) |
| LLM | Groq API (`llama-3.3-70b-versatile`) |
| Language | Python 3.12 |

## How It Works (Architecture)
```
Upload PDF → Extract text (pypdf) → Chunk (800 chars, 150 overlap)
→ Embed chunks (SentenceTransformers) → Store in ChromaDB (with page metadata)

Ask question → Embed question → Retrieve top 4 matching chunks from ChromaDB
→ Build context with page labels → Send to Groq LLM with strict prompt
→ Return answer + cited page numbers
```

See `ARCHITECTURE.md` for full details.

## Setup & Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/ai-document-intelligence.git
cd ai-document-intelligence
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free Groq API key
Sign up at [console.groq.com/keys](https://console.groq.com/keys) and create a key (starts with `gsk_`).

### 4. Create a `.env` file
In the project root, create a file named `.env`:
```
GROQ_API_KEY=gsk_your_real_key_here
```

### 5. Run the app
```bash
uvicorn app:app --reload
```

### 6. Open in browser
Go to **http://127.0.0.1:8000**

## Usage
1. Upload a PDF on the homepage.
2. Wait for the "Document Indexed Successfully" confirmation.
3. Ask a question about the document's content.
4. View the answer along with the page number(s) it was sourced from.

## Sample Questions
See `TEST_CASES.md` and `DEMO_SCRIPT.md` for a full walkthrough with sample Q&A.

## Limitations
- Text-only PDFs (scanned/image-based PDFs need OCR, not yet implemented)
- No multi-document querying yet — one active document at a time
- No authentication / multi-user support
- Chunking is fixed-size, not semantic

## Project Docs
- `ARCHITECTURE.md` — system design details
- `REQUIREMENTS.md` — functional & technical requirements
- `TEST_CASES.md` — test scenarios and results
- `DEMO_SCRIPT.md` — live demo walkthrough
- `LEARNINGS.md` — issues faced and how they were resolved

## Author
Vineet
