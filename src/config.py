import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in your .env file.")

if not SEC_USER_AGENT or "@" not in SEC_USER_AGENT:
    raise ValueError(
        "Invalid or missing SEC_USER_AGENT in your .env file. "
        "SEC EDGAR requires a User-Agent formatted as 'Name email@domain.com'."
    )