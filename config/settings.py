import os
from pathlib import Path
from dotenv import load_dotenv

print("Current working directory:", os.getcwd())  # debug

dotenv_path = Path(__file__).parent.parent / ".env"
print("dotenv_path", dotenv_path)
load_dotenv(dotenv_path)

API_KEY = os.getenv("API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")
DATA_DIR = os.getenv("DATA_DIR")
MAX_CHUNK_CHARS = os.getenv("MAX_CHUNK_CHARS")
ANTIPATTERN_TYPE = os.getenv("ANTIPATTERN_TYPE")

print(f"DATA_DIR loaded: {DATA_DIR}")
