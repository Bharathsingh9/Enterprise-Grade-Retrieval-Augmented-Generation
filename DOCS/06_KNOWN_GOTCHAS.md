# ⚠️ Known Gotchas & Architectural Decisions

This document tracks non-obvious platform quirks and explains why the architecture is designed the way it is.

---

## 1. Logfire Initialization Order (The "Poisoning" Bug)

**The Issue:**
When adding Logfire observability, you might see traces fail to appear in the dashboard, accompanied by the warning:
`No logs or spans will be created until logfire.configure() has been called.`

**The Reason:**
If any module in the application calls `logfire.info()` or `logfire.span()` *before* `logfire.configure()` has been executed, Logfire's internal state becomes "poisoned" for that process. It enters a silent, no-op mode and discards all subsequent traces, even if you call `.configure()` later.

If we were to import `settings` from `app.config` at the top of `app/main.py` to get the `LOGFIRE_TOKEN`, Python's import engine could inadvertently load nested modules (like our reranker or LLM clients) which might contain module-level Logfire calls, triggering this poisoning effect.

**The Solution:**
We bypass the `config.py` file entirely at the very top of `app/main.py`. We load the environment variables directly using `os.getenv()` and configure Logfire **before any other application imports occur**.

```python
# app/main.py
import logfire
import os
from dotenv import load_dotenv

load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))

# Safe to import the rest of the application now!
from app.config import settings 
from app.agents.graph import rag_agent
```
This guarantees that Logfire is fully awake and tracing before the rest of the application is loaded into memory.

---

## 2. The "Lazy Loading" Pattern (FlashRank & Gemini)

**The Issue:**
Loading heavy machine learning models (like FlashRank) or initializing large SDKs (like the Gemini client) at the very top of your files can cause two major problems:
1.  **FastAPI Startup Delays**: The server won't start responding to health checks until the models are loaded.
2.  **Logfire Poisoning**: If these SDKs make any internal calls before Logfire is configured, they can "poison" the process, causing your traces to disappear.

**The Solution:**
We implemented a **Lazy Loading** pattern across the entire application. We do not initialize the Gemini embedding client or the FlashRank ranker at the module level. Instead, we wrap them in "getter" functions that only trigger the first time they are actually needed.

```python
# app/services/retrieval/embedding.py
def get_embedding_model():
    global model
    if model is None:
        # Initialized ONLY on first use!
        model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2-preview",
            google_api_key=settings.GEMINI_API_KEY
        )
    return model
```

This ensures your FastAPI server starts in **milliseconds**, and Logfire is guaranteed to be active before any AI service is touched.
