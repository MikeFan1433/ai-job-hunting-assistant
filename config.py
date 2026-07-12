"""Configuration settings for AI Job Hunting Assistant."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

# AI Builder API Configuration (from https://space.ai-builders.com/backend/openapi.json)
AI_BUILDER_BASE_URL = os.getenv(
    "AI_BUILDER_BASE_URL",
    "https://space.ai-builders.com/backend"
)

# Try multiple possible environment variable names for API key
STUDENT_PORTAL_API_KEY = (
    os.getenv("AI_BUILDER_TOKEN") or  # Primary: AI_BUILDER_TOKEN
    os.getenv("AI_BUILDER_API_KEY") or
    os.getenv("STUDENT_PORTAL_API_KEY") or
    os.getenv("AI_BUILDER_API_TOKEN") or
    os.getenv("SUPER_MIND_API_KEY") or
    os.getenv("OPENAI_API_KEY")
)

# Backward compatibility
STUDENT_PORTAL_BASE_URL = AI_BUILDER_BASE_URL

# OpenAI Configuration (if using OpenAI directly)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LLM Model Configuration
# Use gpt-5 for all agents: AI Builder API passthrough to OpenAI; supports response_format JSON mode for reliable JSON output
LLM_MODEL_JSON = os.getenv("LLM_MODEL_JSON", "gpt-5")  # Model with JSON mode for agents that require structured output
LLM_MODEL = os.getenv("LLM_MODEL", LLM_MODEL_JSON)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4000"))
# OpenAI-compatible JSON mode: ensures output is valid JSON (gpt-5 enforces temperature=1.0 on server).
# Set DISABLE_JSON_MODE=1 to omit response_format if your provider does not support it.
RESPONSE_FORMAT_JSON = {"type": "json_object"} if os.getenv("DISABLE_JSON_MODE") != "1" else None

# Embedding Model Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Vector Database Configuration
VECTOR_DB_PATH = str(BASE_DIR / "data" / "vector_db")
VECTOR_DB_INDEX_FILE = str(BASE_DIR / "data" / "vector_db" / "my_notes.index")
VECTOR_DB_METADATA_FILE = str(BASE_DIR / "data" / "vector_db" / "metadata.json")

# Data Directories
DATA_DIR = str(BASE_DIR / "data")
RESUMES_DIR = str(BASE_DIR / "data" / "resumes")
PROJECTS_DIR = str(BASE_DIR / "data" / "projects")
JOBS_DIR = str(BASE_DIR / "data" / "jobs")

# Agent 2: set AGENT2_FAST_MODE=1 for ~30–60s single-call mode (no follow-up API calls; may be less complete)
# Default to fast mode to improve time-to-first-result in the MVP path.
AGENT2_FAST_MODE = os.getenv("AGENT2_FAST_MODE", "1").strip().lower() in ("1", "true", "yes")
# Agent 2 parallel_20s: grok-4-fast supports response_format json_object natively (~15s).
# gemini-3-flash-preview wraps output in markdown fences which breaks json_object mode.
AGENT2_FAST_MODEL = os.getenv("AGENT2_FAST_MODEL", "grok-4-fast")
# Agent 3: optional fast model when read_timeout_sec is set (avoids empty response from slow gpt-5)
AGENT3_FAST_MODEL = os.getenv("AGENT3_FAST_MODEL", "grok-4-fast")

# ---------------------------------------------------------------------------
# AI Builder chat models (from https://space.ai-builders.com/backend/openapi.json)
# Use for Agent 4 fast path (jd_resume_only + short timeout) without sacrificing quality:
#
#   deepseek               Fast and cost-effective; good for structured JSON. Try: AGENT4_FAST_MODEL=deepseek
#   gemini-3-flash-preview Fast Gemini reasoning (~3–5s typical). Default for Agent 4 fast path.
#   grok-4-fast            Passthrough to X.AI Grok; name suggests low latency. Try: AGENT4_FAST_MODEL=grok-4-fast
#   gemini-2.5-pro         Stronger Gemini; use when timeout is relaxed (e.g. 60–120s).
#   gpt-5                  Best quality, long reasoning; enforces temperature=1.0, needs max_tokens>=1000; often >60s.
#   kimi-k2.5              Multimodal (vision); temperature=1.0 only. Not ideal for resume JSON.
#   supermind-agent-v1     Multi-tool agent (web search); not for single completion.
#
# If Agent 4 still times out with gemini-3-flash-preview, set AGENT4_FAST_MODEL=deepseek or
# AGENT4_FAST_MODEL=grok-4-fast and re-run; use jd_resume_only=True to keep payload small.
# ---------------------------------------------------------------------------
AGENT4_FAST_MODEL = os.getenv("AGENT4_FAST_MODEL", "grok-4-fast")

# Agent 5: use fast model when fast_run=True or short timeout to achieve <30s.
AGENT5_FAST_MODEL = os.getenv("AGENT5_FAST_MODEL", "grok-4-fast")

# Agent 5 (interview prep) enabled by default.
AGENT5_DISABLED = os.getenv("AGENT5_DISABLED", "0").strip().lower() in ("1", "true", "yes")

# Skip Agent 5 during initial workflow; run once after user confirms resume (saves cost + uses final resume).
AGENT5_SKIP_IN_WORKFLOW = os.getenv("AGENT5_SKIP_IN_WORKFLOW", "1").strip().lower() in ("1", "true", "yes")

# Create directories if they don't exist
for directory in [DATA_DIR, RESUMES_DIR, PROJECTS_DIR, JOBS_DIR, VECTOR_DB_PATH]:
    os.makedirs(directory, exist_ok=True)
