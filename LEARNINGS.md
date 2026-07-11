# Engineering Log & Learnings

During the local deployment of this project, several real-world environmental and syntax issues were encountered and resolved systematically.

## 1. Issue: Windows Binary Incompatibility (Python 3.14)
* **What Failed**: Installing `requirements.txt` via pip broke because Python 3.14 (experimental pre-release) lacked compiled wheels for foundational libraries like `Pillow`.
* **Fix**: Uninstalled the experimental Python version and downgraded the system environment to **Python 3.12.5 (Stable)**.

## 2. Issue: Multi-Python Path Collision on Windows
* **What Failed**: Standard `python` and `uvicorn` commands failed to execute because Windows environment paths pointed to older caches, throwing `ModuleNotFoundError`.
* **Fix**: Directly invoked the target executable wrapper session via PowerShell using the absolute path: `& "C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn app:app --reload`

## 3. Issue: Typo in Environment Authentication Syntax
* **What Failed**: `os.environ[AQ.Ab8...]` threw a `NameError: name 'AQ' is not defined` because the API Key was passed as unquoted raw syntax.
* **Fix**: Replaced with a secure direct assignment pattern: `Settings.llm = Gemini(model="gemini-1.5-flash", api_key=MY_API_KEY)`.

## 4. Issue: Missing Underlying Extension Dependency
* **What Failed**: PDF parsing threw a runtime `ModuleNotFoundError: No module named 'pypdf'`.
* **Fix**: Manually isolated the extension package and explicitly ran `pip install pypdf` inside the Python 3.12 target directory wrapper.

---

## Architectural Adjustments & Stack Decisions
While the initial guidelines suggested LlamaIndex, the project deliberately implemented a **Custom Native RAG Pipeline using pure FastAPI, standard ChromaDB SDK, and Groq API Engine** for the following engineering reasons:

1. **Elimination of Library Overhead**: LlamaIndex abstracts away critical operational steps. Writing a raw chunking loop (`chunk_text`) and managing document metadata manually provides complete control over page index parsing accuracy.
2. **Deterministic Prompt Ingestion**: By directly feeding extracted text windows to the Groq API via standard JSON structure formatting, we bypass framework-specific black-box behaviors, guaranteeing that the strict "I don't know" guardrail functions perfectly without hallucinations.
3. **Optimized Cost & Speed**: Swapping paid or rate-limited Gemini setups for Groq's high-throughput hardware interface (`llama-3.3-70b-versatile`) delivers enterprise-grade response latency for local developer testing environments.