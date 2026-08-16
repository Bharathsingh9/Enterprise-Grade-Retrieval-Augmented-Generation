import logfire
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import groq

from app.config import settings


# Production gateway config:
#   - Fallback: primary @rag/llama-3.3-70b-versatile → @brag/llama-3.1-8b-instant on failure
#   - Cache: semantic mode (requires Portkey Enterprise — silently falls back to simple on free/starter)
#   - Retry: 2 attempts on rate limit / server error before triggering the fallback target
GATEWAY_CONFIG = {
    "strategy": {"mode": "fallback"},
    "cache": {"mode": "simple"},
    "retry": {
        "attempts": 2,
        "on_status_codes": [429, 503]
    },
    "targets": [
        {"override_params": {"model": f"@{settings.GROQ_SLUG}/llama-3.3-70b-versatile"}},
        {"override_params": {"model": f"@{settings.GROQ_SLUG_2}/llama-3.1-8b-instant"}},
    ]
}

_raw_portkey_client = Portkey(
    api_key=settings.PORTKEY_API_KEY or "dummy_key"
)


class FallbackChatLLM:
    """
    Wraps LangChain LLM: tries Portkey ChatOpenAI first, falls back to direct ChatGroq.
    """
    def __init__(self, feature: str = "rag"):
        self.feature = feature
        self.portkey_llm = ChatOpenAI(
            api_key=settings.PORTKEY_API_KEY or "dummy_key",
            base_url=PORTKEY_GATEWAY_URL,
            model=f"@{settings.GROQ_SLUG}/llama-3.3-70b-versatile",
            temperature=0,
            default_headers=createHeaders(
                api_key=settings.PORTKEY_API_KEY or "dummy_key",
                metadata={
                    "feature": feature,
                    "_user": "rag-system",
                    "environment": "production"
                }
            )
        )
        self.groq_llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0
        )

    def invoke(self, input_data, config=None, **kwargs):
        try:
            return self.portkey_llm.invoke(input_data, config=config, **kwargs)
        except Exception as e:
            logfire.warning("⚠️ Portkey Gateway call failed ({error}). Falling back to direct Groq LLM.", error=str(e))
            return self.groq_llm.invoke(input_data, config=config, **kwargs)


class FallbackCompletions:
    def __init__(self, raw_portkey):
        self.raw_portkey = raw_portkey
        self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)

    def create(self, **kwargs):
        try:
            return self.raw_portkey.chat.completions.create(**kwargs)
        except Exception as e:
            logfire.warning("⚠️ Portkey client failed ({error}). Falling back to direct Groq client.", error=str(e))
            model = kwargs.get("model", settings.GROQ_MODEL)
            if not model or model.startswith("@"):
                model = settings.GROQ_MODEL
            kwargs["model"] = model
            return self.groq_client.chat.completions.create(**kwargs)


class FallbackChat:
    def __init__(self, raw_portkey):
        self.completions = FallbackCompletions(raw_portkey)


class FallbackPortkeyClient:
    def __init__(self, raw_portkey):
        self.chat = FallbackChat(raw_portkey)


portkey_client = FallbackPortkeyClient(_raw_portkey_client)


def get_langchain_llm(feature: str = "rag"):
    return FallbackChatLLM(feature=feature)


def extract_cache_status(response) -> str:
    """
    Pull x-portkey-cache-status from the Portkey native client response headers.
    Tries multiple attribute paths defensively — returns 'MISS' if not found.
    """
    for attr in ("_raw_response", "_response", "_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            status = getattr(raw, "headers", {}).get("x-portkey-cache-status", "")
            if status:
                return status.upper()
    return "MISS"