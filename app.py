import os
import logging
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import pypdf
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

load_dotenv()

# Proper Basic Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Document Intelligence")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("Initialization Failed: GROQ_API_KEY is missing in the .env file.")
    raise RuntimeError("Set GROQ_API_KEY in your .env file")
groq_client = Groq(api_key=GROQ_API_KEY)

UPLOAD_DIR = "./temp_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ChromaDB setup with built-in embedding function (all-MiniLM-L6-v2)
logger.info("Initializing ChromaDB persistent store...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.get_or_create_collection(name="documents", embedding_function=embed_fn)
logger.info("ChromaDB vector space and embeddings loaded successfully.")


def chunk_text(pages_text, chunk_size=800, overlap=150):
    """pages_text: list of (page_number, text). Returns list of (chunk, page_number)."""
    logger.info("Starting document text chunking process...")
    chunks = []
    for page_num, text in pages_text:
        text = text.strip()
        if not text:
            continue
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append((chunk, page_num))
            start += chunk_size - overlap
    logger.info(f"Chunking completed. Total chunks generated: {len(chunks)}")
    return chunks


@app.get("/", response_class=HTMLResponse)
async def read_root():
    logger.info("Root endpoint accessed - serving Neptune Blue dashboard UI.")
    return """
    <html>
        <head><title>AI Document Intelligence</title></head>
        <style>
    /* Neptune Blue Theme Variables */
    :root {
        --neptune-dark: #0f172a;       /* Deep space/ocean background */
        --neptune-card: #1e293b;       /* Card background */
        --neptune-primary: #0284c7;    /* Vibrant Neptune Blue */
        --neptune-hover: #0369a1;      /* Darker blue for hover states */
        --neptune-text: #f8fafc;       /* Bright text */
        --neptune-muted: #94a3b8;      /* Secondary text */
        --neptune-border: #334155;     /* Subtle borders */
    }

    /* Overall Page Style Overrides */
    body {
        background-color: var(--neptune-dark) !important;
        color: var(--neptune-text) !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
        background-image: radial-gradient(circle at 50% 0%, #0c4a6e 0%, var(--neptune-dark) 70%);
        min-height: 100vh;
    }

    /* Container Box */
    body {
        border: 1px solid var(--neptune-border) !important;
        background-color: var(--neptune-card) !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
    }

    /* Typography */
    h2 {
        color: #38bdf8;
        border-bottom: 2px solid var(--neptune-border);
        padding-bottom: 12px;
        margin-top: 0;
        font-weight: 600;
        letter-spacing: -0.5px;
    }

    label {
        color: var(--neptune-muted);
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 4px;
    }

    hr {
        border: 0 !important;
        height: 1px !important;
        background-color: var(--neptune-border) !important;
        margin: 24px 0 !important;
    }

    /* Input Fields */
    input[type="file"], input[type="text"] {
        display: block;
        width: 100%;
        box-sizing: border-box;
        background-color: var(--neptune-dark) !important;
        border: 1px solid var(--neptune-border) !important;
        color: var(--neptune-text) !important;
        border-radius: 6px !important;
        padding: 10px 12px !important;
        transition: all 0.2s ease;
    }

    input[type="text"]::placeholder {
        color: #64748b;
    }

    input[type="text"]:focus, input[type="file"]:focus {
        outline: none !important;
        border-color: var(--neptune-primary) !important;
        box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.25) !important;
    }

    /* Buttons */
    button[type="submit"] {
        background-color: var(--neptune-primary) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 16px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: background-color 0.15s ease, transform 0.1s ease !important;
        width: 100%;
        margin-top: 8px;
        font-size: 0.95rem;
    }

    button[type="submit"]:hover {
        background-color: var(--neptune-hover) !important;
    }

    button[type="submit"]:active {
        transform: scale(0.98);
    }
</style>
        <body style="font-family: Arial; max-width: 600px; margin: 40px auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px;">
            <h2>AI Document Intelligence </h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <label><b>Step 1: Upload PDF File</b></label><br/><br/>
                <input type="file" name="file" accept=".pdf" required><br/><br/>
                <button type="submit">Upload your document!!</button>
            </form>
            <br/><hr/><br/>
            <form action="/query" method="post">
                <label><b>Step 2: Ask a Question</b></label><br/><br/>
                <input type="text" name="query" placeholder="Ask something..." required style="width: 100%; padding: 8px;"><br/><br/>
                <button type="submit">submit your query!!</button>
            </form>
        </body>
    </html>
    """


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        logger.info(f"File upload request received for: {file.filename}")
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File successfully saved locally at: {file_path}")

        logger.info(f"Starting text extraction from PDF via PyPDF for: {file.filename}")
        reader = pypdf.PdfReader(file_path)
        pages_text = [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
        logger.info(f"Extracted basic layout from {len(pages_text)} pages.")

        chunks = chunk_text(pages_text)
        if not chunks:
            logger.warning(f"Aborted upload: No readable text context discovered in {file.filename}")
            raise HTTPException(status_code=400, detail="No extractable text found in PDF.")

        logger.info("Preparing vectors, metadata structural payloads for ChromaDB ingestion...")
        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [c[0] for c in chunks]
        metadatas = [{"source": file.filename, "page": c[1]} for c in chunks]

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info(f"Success: Indexed {len(chunks)} text blocks into vector repository from file '{file.filename}'")

        # Neptune Blue Success Layout
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Upload Successful</title>
            <style>
                body {{
                    background-color: #0f172a;
                    color: #f8fafc;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-image: radial-gradient(circle at 50% 0%, #0c4a6e 0%, #0f172a 70%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                }}
                .card {{
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 12px;
                    padding: 32px;
                    max-width: 500px;
                    width: 90%;
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
                    text-align: center;
                }}
                .icon {{
                    color: #38bdf8;
                    font-size: 48px;
                    margin-bottom: 16px;
                }}
                h2 {{ color: #38bdf8; margin-top: 0; }}
                p {{ color: #94a3b8; line-height: 1.6; font-size: 0.95rem; }}
                .btn {{
                    display: inline-block;
                    background-color: #0284c7;
                    color: white;
                    text-decoration: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: 600;
                    margin-top: 20px;
                    transition: background-color 0.2s;
                }}
                .btn:hover {{ background-color: #0369a1; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">✓</div>
                <h2>Document Indexed Successfully</h2>
                <p>Uploaded <strong>{file.filename}</strong> split into <strong>{len(chunks)} chunks</strong> across <strong>{len(pages_text)} pages</strong>.</p>
                <a href="/" class="btn">Go to Dashboard</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Critical execution fault during upload route: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query_document(query: str = Form(...)):
    try:
        logger.info(f"Incoming user query request: '{query}'")
        logger.info("Executing vector similarity vector-query via ChromaDB...")
        results = collection.query(query_texts=[query], n_results=4)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        if not docs:
            logger.warning("Empty search database space. Prompted execution fallback trigger.")
            answer_text = "I don't know. No document has been uploaded yet."
            source_pages = []
        else:
            logger.info(f"ChromaDB returned {len(docs)} matching contextual documents. Constructing synthesis window.")
            context = "\n\n".join(
                f"[Page {m['page']}]: {d}" for d, m in zip(docs, metas)
            )

            prompt = f"""You are a strict assistant. Answer the question using ONLY the context below.
If the answer is not present in the context, reply exactly: "I don't know based on the provided document."
Cite the page number(s) you used.

Context:
{context}

Question: {query}"""

            logger.info("Dispatching optimized system orchestration frame to Groq API...")
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            answer_text = response.choices[0].message.content
            source_pages = sorted(set(m["page"] for m in metas))
            logger.info("Groq API successfully processed and synthesized response matrix.")

        logger.info(f"Final Execution Logging Metrics -> Query: {query} | Page References: {source_pages}")

        # Neptune Blue Query Results Layout
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Query Result</title>
            <style>
                body {{
                    background-color: #0f172a;
                    color: #f8fafc;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-image: radial-gradient(circle at 50% 0%, #0c4a6e 0%, #0f172a 70%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                    padding: 20px;
                    box-sizing: border-box;
                }}
                .card {{
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 12px;
                    padding: 32px;
                    max-width: 650px;
                    width: 100%;
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
                }}
                h2 {{ color: #38bdf8; margin-top: 0; border-bottom: 1px solid #334155; padding-bottom: 12px; font-size: 1.4rem; }}
                .section-title {{ color: #64748b; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 20px; margin-bottom: 6px; font-weight: bold; }}
                .query-text {{ color: #e2e8f0; font-style: italic; font-size: 1.05rem; background: #0f172a; padding: 10px 14px; border-radius: 6px; border-left: 3px solid #0284c7; }}
                .answer-text {{ color: #f8fafc; line-height: 1.6; font-size: 1rem; white-space: pre-line; }}
                .meta-badge {{ display: inline-block; background-color: #0c4a6e; color: #38bdf8; padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; font-weight: 500; border: 1px solid #0284c7; }}
                .actions {{ margin-top: 28px; border-top: 1px solid #334155; padding-top: 16px; display: flex; justify-content: flex-end; }}
                .btn {{
                    background-color: #0284c7;
                    color: white;
                    text-decoration: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: 600;
                    transition: background-color 0.2s;
                }}
                .btn:hover {{ background-color: #0369a1; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>AI Intelligence Response</h2>
                
                <div class="section-title">Your Question</div>
                <div class="query-text">"{query}"</div>
                
                <div class="section-title">Answer</div>
                <div class="answer-text">{answer_text}</div>
                
                <div class="section-title">Sources Used</div>
                <div>
                    <span class="meta-badge">Pages: {', '.join(map(str, source_pages)) if source_pages else 'None'}</span>
                </div>
                
                <div class="actions">
                    <a href="/" class="btn">Ask Another Question</a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Critical execution fault during query routing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))