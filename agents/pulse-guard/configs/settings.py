import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Base Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
PROMPTS_DIR = BASE_DIR / "prompts"

# --- Anthropic / LLM ---
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# --- Application ---
APP_ENV: str = os.getenv("APP_ENV", "development")
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

# --- HITL Gate ---
# Priority levels that trigger the Human-in-the-Loop approval gate
HITL_TRIGGER_PRIORITIES: list[str] = ["Urgent", "Safety"]

# --- Observability ---
PERF_LOG_PATH: Path = DOCS_DIR / "performance-audit.log"
PROTOCOLS_PATH: Path = DATA_DIR / "protocols.json"
SAFETY_PERSONA_PATH: Path = PROMPTS_DIR / "safety-persona.md"

# --- API Internal Auth ---
# Used to authenticate the Streamlit frontend when approving HITL actions
INTERNAL_API_KEY: str = os.environ["INTERNAL_API_KEY"]
