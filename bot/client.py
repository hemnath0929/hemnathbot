import asyncio
import logging
import time
import discord
from discord.ext import commands
import aiohttp

from config import SYSTEM_INSTRUCTION, GMAIL_CHECK_INTERVAL_MINUTES
from models import ModelRouter
from utils import MemoryManager, ReminderManager, TokenTracker, generate_morning_briefing
from bot.channels import ensure_server_channels, get_channel_config
from .commands import register_commands

logger = logging.getLogger(__name__)

class AgentBot(commands.Bot):
    """Discord Bot Client managing events, channel personas, natural reminders, and daily briefing."""

    def __init__(
        self,
        router: ModelRouter,
        memory: MemoryManager,
        reminders: ReminderManager,
        token_tracker: TokenTracker,
    ):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)
        self.router = router
        self.memory = memory
        self.reminders = reminders
        self.token_tracker = token_tracker
        self.session: aiohttp.ClientSession = None
        self.last_briefing_date: str = ""
        self.seen_email_ids: set = set()
        self.google_auth_done: bool = False

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        register_commands(self.tree, self.router, self.memory, self.reminders, self.token_tracker)
        await self.tree.sync()
        logger.info("Synced Slash Commands.")

        asyncio.create_task(self.reminders.start_loop(self.send_reminder_notification))
        asyncio.create_task(self.daily_briefing_loop())
        asyncio.create_task(self.gmail_monitor_loop())

    async def on_ready(self):
        logger.info(f"Bot connected as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="commands | /briefing | /help"
            )
        )

        for guild in self.guilds:
            try:
                await ensure_server_channels(guild)
            except Exception as e:
                logger.error(f"Error auto-creating channels in {guild.name}: {e}")

    async def on_guild_join(self, guild: discord.Guild):
        await ensure_server_channels(guild)

    async def send_reminder_notification(self, channel_id: int, user_id: int, message: str):
        try:
            channel = self.get_channel(channel_id)
            if not channel:
                channel = await self.fetch_channel(channel_id)
            if channel:
                await channel.send(f"🔔 <@{user_id}> **Reminder Alert:** {message}")
        except Exception as e:
            logger.error(f"Failed to send reminder notification: {e}")

    async def daily_briefing_loop(self):
        """Background loop to send Daily Morning Briefing at 8:00 AM."""
        while True:
            try:
                now_struct = time.localtime()
                current_time = time.strftime("%H:%M", now_struct)
                today_date = time.strftime("%Y-%m-%d", now_struct)

                if current_time == "08:50" and self.last_briefing_date != today_date:
                    self.last_briefing_date = today_date
                    for guild in self.guilds:
                        target_channel = discord.utils.get(guild.text_channels, name="reminders-and-tasks")
                        if not target_channel:
                            target_channel = discord.utils.get(guild.text_channels, name="general-ai")

                        if target_channel:
                            briefing_card = await generate_morning_briefing(self.router, self.reminders)
                            await target_channel.send(briefing_card)

            except Exception as e:
                logger.error(f"Error in daily briefing loop: {e}")

            await asyncio.sleep(40)

    async def gmail_monitor_loop(self):
        """Background loop to check Gmail every N minutes and alert new emails."""
        import os
        if not os.path.exists("credentials.json"):
            logger.info("Gmail monitor: credentials.json not found, skipping.")
            return

        await asyncio.sleep(30)  # Give bot time to fully connect first

        while True:
            try:
                from utils.google_integrations import fetch_important_emails
                emails = await asyncio.get_event_loop().run_in_executor(None, fetch_important_emails, 10)
                self.google_auth_done = True

                new_emails = [e for e in emails if e["id"] not in self.seen_email_ids]

                if new_emails:
                    for guild in self.guilds:
                        # Post to #email-alerts or fallback to #general-ai
                        target = (
                            discord.utils.get(guild.text_channels, name="email-alerts")
                            or discord.utils.get(guild.text_channels, name="general-ai")
                        )
                        if target:
                            for email in new_emails[:3]:
                                self.seen_email_ids.add(email["id"])
                                alert_msg = (
                                    f"📩 **New Email Alert!**\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"👤 **From:** `{email['from']}`\n"
                                    f"📌 **Subject:** {email['subject']}\n"
                                    f"📝 *{email['snippet'][:200]}...*\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"_Use `/gmail` to view all unread emails._"
                                )
                                await target.send(alert_msg)
                else:
                    # Still mark seen
                    for e in emails:
                        self.seen_email_ids.add(e["id"])

            except Exception as e:
                if "credentials" not in str(e).lower() and "token" not in str(e).lower():
                    logger.error(f"Gmail monitor error: {e}")

            await asyncio.sleep(GMAIL_CHECK_INTERVAL_MINUTES * 60)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.user in message.mentions

        if not (is_dm or is_mentioned or not message.content.startswith("!")):
            return

        prompt = message.content.replace(f"<@{self.user.id}>", "").strip()

        image_bytes_list = []
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    try:
                        img_bytes = await attachment.read()
                        image_bytes_list.append(img_bytes)
                    except Exception as e:
                        logger.error(f"Error downloading attachment: {e}")

        if not prompt and not image_bytes_list:
            return

        if not prompt and image_bytes_list:
            prompt = "Please describe or analyze this image."

        async with message.channel.typing():
            channel_id = message.channel.id
            channel_name = getattr(message.channel, "name", "general-ai")

            # Special Natural Language Reminder Parsing for #reminders-and-tasks or keywords
            is_reminder_channel = channel_name in ["reminders-and-tasks", "general-ai"]
            has_remind_keyword = any(k in prompt.lower() for k in ["remind", "reminder", "schedule", "alarm", "timer"])

            if is_reminder_channel and has_remind_keyword:
                is_rem, rem_data = await self.reminders.parse_natural_reminder(prompt, self.router, channel_id)
                if is_rem and rem_data.get("delay_seconds", 0) > 0:
                    delay_sec = rem_data["delay_seconds"]
                    rem_msg = rem_data.get("message", prompt)
                    formatted_t = rem_data.get("formatted_time", f"in {delay_sec // 60} minutes")

                    self.reminders.add_reminder(channel_id, message.author.id, rem_msg, delay_sec)

                    card = (
                        f"⏰ **Reminder Scheduled Successfully!**\n"
                        f"• **For:** <@{message.author.id}>\n"
                        f"• **Time:** `{formatted_t}`\n"
                        f"• **Task:** *\"{rem_msg}\"*\n\n"
                        f"I will ping you right here when the time comes! 🔔"
                    )
                    await message.channel.send(card)
                    return

            default_model, channel_prompt = get_channel_config(channel_name)

            if channel_id not in self.router.active_model_per_channel:
                self.router.set_active_model(channel_id, default_model)

            combined_system = f"{SYSTEM_INSTRUCTION}\n\n{channel_prompt}".strip()

            self.memory.add_message(channel_id, "user", prompt)
            history = self.memory.get_history(channel_id)[:-1]

            response, provider_name, tokens = await self.router.generate(
                channel_id=channel_id,
                prompt=prompt,
                history=history,
                image_bytes_list=image_bytes_list,
                system_instruction=combined_system,
            )

            if not response.startswith("❌"):
                self.memory.add_message(channel_id, "assistant", response)

            full_reply = f"{response}\n\n*_Powered by {provider_name} ({tokens:,} tokens)_*"
            await self._send_chunked_message(message.channel, full_reply)

    async def _send_chunked_message(self, destination, text: str):
        max_len = 1950
        if len(text) <= max_len:
            await destination.send(text)
            return

        chunks = [text[i : i + max_len] for i in range(0, len(text), max_len)]
        for chunk in chunks:
            await destination.send(chunk)
            await asyncio.sleep(0.5)

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()
