import sys
import logging
import asyncio
import os
from aiohttp import web

from config import (
    DISCORD_TOKEN,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    DEEPSEEK_API_KEY,
    DEFAULT_MODEL,
)
from models import ModelRouter
from utils import MemoryManager, ReminderManager, TokenTracker
from bot import AgentBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("Main")

async def start_health_check_server():
    """Starts a lightweight web server for Render/Railway health checks."""
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", lambda req: web.Response(text="Hemnath Bot is live & running 24/7!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check HTTP server running on port {port}")

async def main():
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is missing in .env file! Exiting.")
        sys.exit(1)

    logger.info("Initializing TokenTracker & Multi-LLM Router...")
    token_tracker = TokenTracker(db_path="token_usage.db")
    router = ModelRouter(
        gemini_key=GEMINI_API_KEY,
        openai_key=OPENAI_API_KEY,
        deepseek_key=DEEPSEEK_API_KEY,
        token_tracker=token_tracker,
        default_provider=DEFAULT_MODEL,
    )

    memory = MemoryManager(max_history=10)
    reminders = ReminderManager(db_path="reminders.db")

    logger.info("Starting Health Check Web Server...")
    await start_health_check_server()

    logger.info("Starting Antigravity Multi-Channel AI Agent...")
    bot = AgentBot(
        router=router,
        memory=memory,
        reminders=reminders,
        token_tracker=token_tracker,
    )

    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped by user.")

