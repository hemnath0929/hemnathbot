import discord
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Channel definitions: (name, topic, default_model, system_prompt_extra)
CHANNELS_CONFIG = [
    (
        "general-ai",
        "💬 General AI chat assistant for rapid Q&A and daily doubts.",
        "gemini",
        "You are in #general-ai. Be helpful, quick, and conversational.",
    ),
    (
        "code-lab",
        "💻 Coding & Development hub. Code review, debugging, and algorithms.",
        "deepseek",
        "You are in #code-lab, an expert Senior Software Developer persona. Provide clean, well-formatted code snippets with explanations.",
    ),
    (
        "reminders-and-tasks",
        "⏰ Automated schedule, To-Dos, and Reminder notifications.",
        "gemini",
        "You are in #reminders-and-tasks. Help the user schedule tasks, manage time, and keep track of daily routines.",
    ),
    (
        "web-research",
        "🔍 Web search, live news, and research synthesis.",
        "gemini",
        "You are in #web-research. Synthesize accurate research summaries and analyze provided links.",
    ),
    (
        "expense-tracker",
        "💰 Expense logging and financial calculations.",
        "gpt",
        "You are in #expense-tracker. Extract cost items, calculate totals, and log expenses clearly.",
    ),
    (
        "second-brain",
        "🧠 Personal knowledge base, notes, and password store.",
        "gemini",
        "You are in #second-brain. Save and recall personal notes, facts, and project ideas efficiently.",
    ),
    (
        "image-studio",
        "🖼️ Vision analysis, diagram reading, and OCR text extraction.",
        "gemini",
        "You are in #image-studio. Analyze attached photos, extract text from documents, and describe visual content.",
    ),
]

async def ensure_server_channels(guild: discord.Guild):
    """Ensures all 7 dedicated channels exist in the given Discord server guild."""
    existing_channels = {c.name.lower(): c for c in guild.text_channels}

    for name, topic, _, _ in CHANNELS_CONFIG:
        if name not in existing_channels:
            try:
                channel = await guild.create_text_channel(name=name, topic=topic)
                logger.info(f"Created channel: #{name} in {guild.name}")
            except Exception as e:
                logger.error(f"Failed to create channel #{name}: {e}")

def get_channel_config(channel_name: str) -> Tuple[str, str]:
    """Returns (default_model, extra_prompt) for a given channel name."""
    clean_name = channel_name.lower()
    for name, _, model, prompt in CHANNELS_CONFIG:
        if name == clean_name:
            return model, prompt
    return "gemini", ""
