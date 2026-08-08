import asyncio
import logging
import sqlite3
import time
import json
from typing import Callable, Awaitable, Dict, Any, Tuple

logger = logging.getLogger(__name__)

DB_PATH = "reminders.db"

class ReminderManager:
    """SQLite-backed async reminder scheduler supporting relative and absolute timestamps."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                remind_at REAL NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def add_reminder(self, channel_id: int, user_id: int, message: str, delay_seconds: float) -> float:
        remind_at = time.time() + delay_seconds
        return self.add_reminder_at(channel_id, user_id, message, remind_at)

    def add_reminder_at(self, channel_id: int, user_id: int, message: str, remind_at: float) -> float:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (channel_id, user_id, message, remind_at) VALUES (?, ?, ?, ?)",
            (channel_id, user_id, message, remind_at),
        )
        conn.commit()
        conn.close()
        return remind_at

    def get_pending_reminders_for_user(self, user_id: int) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = time.time()
        cursor.execute(
            "SELECT message, remind_at FROM reminders WHERE user_id = ? AND remind_at > ? ORDER BY remind_at ASC",
            (user_id, now),
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    async def parse_natural_reminder(self, prompt: str, router, channel_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Uses Gemini to parse natural language reminder expressions into delay seconds and message."""
        current_time_str = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())
        system_prompt = (
            f"Current local time: {current_time_str}.\n"
            "Analyze the user prompt to check if it's a request to set a reminder or task timer.\n"
            "If it IS a reminder request, extract:\n"
            "1. 'is_reminder': true\n"
            "2. 'delay_seconds': integer seconds from now until the reminder time\n"
            "3. 'message': reminder text\n"
            "4. 'formatted_time': human friendly string of when it will trigger (e.g. 'Today at 5:30 PM' or 'In 30 minutes')\n"
            "Respond ONLY with a raw JSON object like:\n"
            '{"is_reminder": true, "delay_seconds": 1800, "message": "drink water", "formatted_time": "In 30 minutes"}\n'
            "If it is NOT a reminder request, respond with:\n"
            '{"is_reminder": false}'
        )

        try:
            res_text, _, _ = await router.generate(
                channel_id=channel_id,
                prompt=prompt,
                system_instruction=system_prompt,
            )

            # Strip markdown code blocks if any
            cleaned_json = res_text.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json[7:]
            if cleaned_json.startswith("```"):
                cleaned_json = cleaned_json[3:]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json[:-3]
            cleaned_json = cleaned_json.strip()

            data = json.loads(cleaned_json)
            if data.get("is_reminder") and data.get("delay_seconds", 0) > 0:
                return True, data
        except Exception as e:
            logger.error(f"Error parsing natural reminder: {e}")

        return False, {}

    async def start_loop(self, callback: Callable[[int, int, str], Awaitable[None]]):
        """Runs background loop to check and trigger due reminders."""
        while True:
            try:
                now = time.time()
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, channel_id, user_id, message FROM reminders WHERE remind_at <= ?", (now,))
                rows = cursor.fetchall()

                if rows:
                    ids_to_delete = [r[0] for r in rows]
                    cursor.execute(f"DELETE FROM reminders WHERE id IN ({','.join('?' * len(ids_to_delete))})", ids_to_delete)
                    conn.commit()

                conn.close()

                for _, channel_id, user_id, message in rows:
                    asyncio.create_task(callback(channel_id, user_id, message))

            except Exception as e:
                logger.error(f"Error in reminder loop: {e}")

            await asyncio.sleep(5)
