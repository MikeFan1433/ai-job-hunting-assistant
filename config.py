"""Configuration settings for AI Job Hunting Assistant."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

# Student Portal API Configuration
STUDENT_PORTAL_BASE_URL = os.getenv(
    "STUDENT_PORTAL_BASE_URL",
    "https://space.ai-builders.com/backend"
)

# Try multiple possible environment variable names for API key
STUDENT_PORTAL_API_KEY = (
    os.getenv("STUDENT_PORTAL_API_KEY") or
    os.getenv("AI_BUILDER_TOKEN") or
    os.getenv("AI_BUILDER_API_TOKEN") or
    os.getenv("SUPER_MIND_API_KEY") or
    os.getenv("OPENAI_API_KEY")
)

# OpenAI Configuration (if using OpenAI directly)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LLM Model Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "supermind-agent-v1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4000"))

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

# Create directories if they don't exist
for directory in [DATA_DIR, RESUMES_DIR, PROJECTS_DIR, JOBS_DIR, VECTOR_DB_PATH]:
    os.makedirs(directory, exist_ok=True)
