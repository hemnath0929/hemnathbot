import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini").lower()

SYSTEM_INSTRUCTION = (
    "You are a helpful, highly capable, intelligent Personal AI Agent named Antigravity. "
    "You assist the user with daily tasks, coding, problem solving, creative ideas, and scheduling. "
    "Respond in a natural, friendly, clear, and helpful manner. "
    "Keep responses concise and well-formatted for Discord."
)

GOOGLE_SHEETS_URL = os.getenv("GOOGLE_SHEETS_URL", "")
GMAIL_CHECK_INTERVAL_MINUTES = int(os.getenv("GMAIL_CHECK_INTERVAL_MINUTES", "5"))
WEATHER_CITY = os.getenv("WEATHER_CITY", "Coimbatore")
