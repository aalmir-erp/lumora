import os
from typing import Literal

Backend = Literal["gemini-pro", "gemini-flash", "gemini-cu", "claude-cu"]
Runtime = Literal["railway", "local", "hybrid"]
Mode = Literal["browser", "desktop"]

BACKEND_MODELS: dict[str, str] = {
    "gemini-pro": "gemini-2.5-pro",
    "gemini-flash": "gemini-2.5-flash",
    "gemini-cu": "gemini-2.5-computer-use-preview-10-2025",
    "claude-cu": "claude-sonnet-4-6",
}

DEFAULT_BACKEND: Backend = os.getenv("DEFAULT_BACKEND", "gemini-pro")  # type: ignore
DEFAULT_RUNTIME: Runtime = os.getenv("DEFAULT_RUNTIME", "hybrid")  # type: ignore
LOCAL_AGENT_TOKEN = os.getenv("LOCAL_AGENT_TOKEN", "")
STATUS_WEBHOOK_URL = os.getenv("STATUS_WEBHOOK_URL", "")
FORCE_LOCAL_HOSTS = [
    h.strip() for h in os.getenv("FORCE_LOCAL_HOSTS", "web.whatsapp.com").split(",") if h.strip()
]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
