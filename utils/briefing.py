import time
import logging
import json
import urllib.request
import urllib.parse
from typing import Optional

logger = logging.getLogger(__name__)


def fetch_real_weather(city: str) -> str:
    """Fetch live weather from wttr.in for the given city. No API key needed."""
    try:
        encoded_city = urllib.parse.quote(city)
        url = f"https://wttr.in/{encoded_city}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        humidity = current["humidity"]
        description = current["weatherDesc"][0]["value"]
        wind_kmph = current["windspeedKmph"]

        # Weather advice tip
        tip = ""
        desc_lower = description.lower()
        if "rain" in desc_lower or "shower" in desc_lower or "drizzle" in desc_lower:
            tip = "☂️ Carry an umbrella today!"
        elif "thunder" in desc_lower or "storm" in desc_lower:
            tip = "⛈️ Thunderstorm alert! Stay indoors if possible."
        elif "sun" in desc_lower or "clear" in desc_lower or "bright" in desc_lower:
            tip = "🕶️ Sunny day — don't forget sunscreen!"
        elif "cloud" in desc_lower or "overcast" in desc_lower or "mist" in desc_lower:
            tip = "🌤️ Cloudy skies today. A light jacket might help."
        elif int(temp_c) >= 35:
            tip = "🥵 Very hot today! Stay hydrated and avoid peak sun hours."
        elif int(temp_c) <= 20:
            tip = "🧥 It's cool outside. Carry a jacket!"
        else:
            tip = "😊 Pleasant weather ahead. Have a great day!"

        return (
            f"☀️ **{city} Live Weather:**\n"
            f"• 🌡️ Temperature: **{temp_c}°C** (Feels like {feels_like}°C)\n"
            f"• 🌥️ Condition: {description}\n"
            f"• 💧 Humidity: {humidity}%  |  🌬️ Wind: {wind_kmph} km/h\n"
            f"• {tip}"
        )

    except Exception as e:
        logger.error(f"Weather fetch error for {city}: {e}")
        return f"🌤️ **{city} Weather:** Unable to fetch live data. Check internet connection."


async def generate_morning_briefing(router, reminders_mgr, user_id: Optional[int] = None) -> str:
    """Generates a complete Daily Morning Briefing card with real weather."""
    from config import WEATHER_CITY

    date_str = time.strftime("%A, %B %d, %Y", time.localtime())

    # Real weather fetch (runs in sync, fast enough)
    weather_section = fetch_real_weather(WEATHER_CITY)

    # Get pending tasks from DB
    pending = []
    if user_id:
        pending = reminders_mgr.get_pending_reminders_for_user(user_id)

    tasks_summary = ""
    if pending:
        tasks_summary = "\n".join([
            f"• **{r[0]}** (at {time.strftime('%I:%M %p', time.localtime(r[1]))})"
            for r in pending[:5]
        ])
    else:
        tasks_summary = "• _No pending reminders scheduled for today._"

    prompt = (
        "Give me:\n"
        "1. Top 3 AI & Technology News headlines today (3 short bullet points).\n"
        "2. One powerful 1-line Productivity or Coding Tip.\n"
        "Keep it short, concise, and well formatted with emojis."
    )

    try:
        content, provider, _ = await router.generate(
            channel_id=0,
            prompt=prompt,
        )
    except Exception as e:
        logger.error(f"Error fetching briefing AI content: {e}")
        content = "📰 AI & Tech world is buzzing with updates!\n💡 **Tip**: Plan your top 3 tasks before you start working."
        provider = "Gemini"

    card = (
        f"🌅 **GOOD MORNING! DAILY BRIEFING** 🌅\n"
        f"📅 *{date_str}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{weather_section}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 **Your Pending Reminders:**\n"
        f"{tasks_summary}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{content}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Have an amazing & productive day! 🚀\n"
        f"*Powered by {provider}*"
    )
    return card
