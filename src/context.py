# src/context.py
#---------------------------------------------------------------------------------
# Secrets und Root-Path cachen 
#---------------------------------------------------------------------------------
from pathlib import Path
from dotenv import load_dotenv
from os import getenv
#---------------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
load_dotenv() 

USE_TEST = True
PORT = getenv("PORT")

N8N_URL = f"http://localhost:{PORT}"

AUTH = getenv("N8N_BASIC_AUTH_ACTIVE")
USER = getenv("N8N_BASIC_AUTH_USER")
PSWD = getenv("N8N_BASIC_AUTH_PASSWORD")

N8N_API_KEY = getenv("N8N_API_KEY")
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
GROQ_API_KEY = getenv("GROQ_API_KEY")
OLLAMA_API_KEY = getenv("OLLAMA_API_KEY")
