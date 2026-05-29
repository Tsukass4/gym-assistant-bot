import os
from dotenv import load_dotenv

load_dotenv()

# LLM config
LLM_PROVIDER = "ollama"        # "ollama" o "gemini"
OLLAMA_MODEL = "llama3"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Database
DB_PATH = "database/gym.db"

# Gym info
GYM_NAME = "The_Field"       # Cambia esto al nombre real