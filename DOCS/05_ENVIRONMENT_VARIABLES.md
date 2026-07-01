# 🔑 Environment Variables & Configuration

The project uses a `.env` file for local development. All configuration is managed via **Pydantic Settings** in `app/config.py` for strict type safety. Copy `.env.example` to `.env` and fill in your values before running anything.

---

## 🧠 LLMs

| Variable | Description | Example |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Primary key for Groq LLM calls (Planner + Responder nodes) | `gsk_...` |
| `GROQ_FALLBACK_API_KEY` | Second Groq key used by Portkey as the fallback target; can be the same as primary | `gsk_...` |

---

## 🔀 LLM Gateway

| Variable | Description | Example |
| :--- | :--- | :--- |
| `PORTKEY_API_KEY` | API key for Portkey — enables routing, fallback, caching, and observability across all LLM calls | `pk-...` |

---

## 🌐 Gemini Embeddings

| Variable | Description | Example |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API key used to generate 3072-dim embeddings via `gemini-embedding-2-preview` | `AIza...` |

---

## 🗄️ Vector Database

| Variable | Description | Example |
| :--- | :--- | :--- |
| `QDRANT_API_KEY` | Qdrant Cloud access token | `xyz...` |
| `QDRANT_CLUSTER_ENDPOINT` | Full URL of your Qdrant Cloud cluster | `https://your-cluster.cloud.qdrant.io:6333` |

---

## 🕵️ Observability

| Variable | Description | Example |
| :--- | :--- | :--- |
| `LOGFIRE_TOKEN` | Pydantic Logfire token — traces every API call, parsing step, and retrieval span | `logfire_...` |
| `LANGSMITH_API_KEY` | LangSmith token — records LangGraph node transitions, prompts, and token usage | `lsv2_...` |
| `LANGSMITH_PROJECT` | LangSmith project name to group traces | `enterprise_rag` |
| `LANGSMITH_TRACING` | Enable/disable LangSmith tracing | `true` |
| `LANGSMITH_ENDPOINT` | LangSmith API endpoint | `https://api.smith.langchain.com` |

---

## 🧪 Evals

| Variable | Description | Example |
| :--- | :--- | :--- |
| `JUDGE_GROQ` | Separate Groq key used exclusively by the RAGAS eval pipeline as the judge LLM. Keeping it separate ensures eval runs cannot exhaust the production key. | `gsk_...` |

---

## 🖥️ Backend

| Variable | Description | Example |
| :--- | :--- | :--- |
| `BACKEND_URL` | URL the Streamlit UI uses to reach the FastAPI backend | `http://localhost:8000` |

---

## 🔒 Security Best Practices
1.  **Never** commit your `.env` file to Git — it is in `.gitignore`.
2.  Use `.env.example` as the template when onboarding new developers.
3.  Keep `JUDGE_GROQ` on a separate key so eval workloads cannot rate-limit the live app.
