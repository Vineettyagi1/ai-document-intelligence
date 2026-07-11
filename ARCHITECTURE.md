# Architecture - AI Document Intelligence (Groq & ChromaDB Pipeline)

This document details the actual system flow and data components running within the application.

## 1. Data Ingestion Pipeline (Upload)
1. **Upload**: The user uploads a PDF via the FastAPI-based dashboard frontend.
2. **Text Extraction**: The backend processes the file stream using `pypdf` to parse text layout dynamically page-by-page.
3. **Chunking Engine**: The custom chunking function loops through pages, separating text blocks into 800-character segments with a 150-character overlap to keep sentences in context.
4. **Local Vectorization**: Text chunks are passed to the `all-MiniLM-L6-v2` SentenceTransformer embedding function running locally.
5. **Storage Ingestion**: Structural payloads containing structural ID hashes, raw text strings, and dictionary metadatas (`{"source": filename, "page": page_number}`) are committed into a local persistent ChromaDB collection.

## 2. RAG Query Pipeline (Q&A)
1. **User Search Input**: The user submits a natural language question via the UI.
2. **Vector Space Query**: The text string is matched against ChromaDB vector metrics to retrieve the top 4 most relevant chunks.
3. **Context Construction**: Extracted matches are concatenated alongside page headers: `[Page X]: content`.
4. **Strict Orchestration Window**: A custom system prompt passes the data payload into Groq's `llama-3.3-70b-versatile` engine with explicit rules: *“Answer the question using ONLY the context below. If the answer is not present, reply exactly: 'I don't know based on the provided document.'”*
5. **Output Matrix**: The generated text answer and the array list of verified pages are parsed and displayed on the results layout screen.