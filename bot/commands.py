import os
import asyncio
import discord
from discord import app_commands
from typing import Literal
from bot.channels import ensure_server_channels
from utils.briefing import generate_morning_briefing
from config import GOOGLE_SHEETS_URL

def register_commands(tree: app_commands.CommandTree, router, memory, reminders, token_tracker):
    """Registers slash commands to Discord CommandTree."""

    @tree.command(name="briefing", description="Generate live Daily Morning Briefing")
    async def briefing_command(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        briefing_text = await generate_morning_briefing(router, reminders, user_id=interaction.user.id)
        await interaction.followup.send(briefing_text)

    @tree.command(name="model", description="Switch active AI model (gemini, gpt, deepseek)")
    @app_commands.describe(provider="Choose AI provider")
    async def model_command(
        interaction: discord.Interaction,
        provider: Literal["gemini", "gpt", "deepseek"],
    ):
        success = router.set_active_model(interaction.channel_id, provider)
        if success:
            await interaction.response.send_message(
                f"✅ Model switched to **{provider.upper()}** for this channel!",
                ephemeral=False,
            )
        else:
            await interaction.response.send_message(
                f"❌ Unknown provider: {provider}", ephemeral=True
            )

    @tree.command(name="status", description="Show bot status & active model")
    async def status_command(interaction: discord.Interaction):
        active = router.get_active_model_name(interaction.channel_id)
        latency = round(interaction.client.latency * 1000, 2)
        summary = token_tracker.get_summary()
        total_tokens = summary["overall_total"]

        msg = (
            f"🤖 **Antigravity AI Agent Status**\n"
            f"• **Active Model:** `{active.upper()}`\n"
            f"• **Bot Latency:** `{latency} ms`\n"
            f"• **Total Tokens Used:** `{total_tokens:,}`\n"
            f"• **Available Providers:** Gemini, GPT-4o, DeepSeek"
        )
        await interaction.response.send_message(msg)

    @tree.command(name="usage", description="Visual AI token usage stats graph & breakdown")
    async def usage_command(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        summary = token_tracker.get_summary()
        overall = summary["overall_total"]
        providers_data = summary["providers"]

        chart_file = token_tracker.generate_usage_chart(output_path="token_chart.png")

        max_quota = 500000
        ratio = min(overall / max_quota, 1.0)
        filled = int(ratio * 10)
        bar = "█" * filled + "░" * (10 - filled)
        percent = round(ratio * 100, 1)

        breakdown_text = ""
        for prov, stat in providers_data.items():
            breakdown_text += f"• **{prov.capitalize()}**: `{stat['tokens']:,} tokens` ({stat['requests']} requests)\n"

        if not breakdown_text:
            breakdown_text = "_No tokens logged yet._\n"

        text = (
            f"📊 **AI Token Consumption Visual Meter**\n"
            f"`[{bar}]` **{percent}%** (`{overall:,}` tokens used)\n\n"
            f"**Breakdown by Model Provider:**\n"
            f"{breakdown_text}"
        )

        file = discord.File(chart_file, filename="token_chart.png")
        embed = discord.Embed(title="Token Usage Graph", color=0x4285F4)
        embed.set_image(url="attachment://token_chart.png")

        await interaction.followup.send(content=text, file=file, embed=embed)

    @tree.command(name="setup_channels", description="Auto-create 7 dedicated AI channels in server")
    async def setup_channels_command(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return

        await interaction.response.send_message("⚙️ Creating dedicated AI channels...", ephemeral=True)
        await ensure_server_channels(interaction.guild)
        await interaction.followup.send("✅ All 7 channels created successfully!")

    @tree.command(name="clear", description="Clear conversation history context")
    async def clear_command(interaction: discord.Interaction):
        memory.clear(interaction.channel_id)
        await interaction.response.send_message("🧹 Conversation history cleared!", ephemeral=False)

    @tree.command(name="remind", description="Set a timer reminder")
    @app_commands.describe(minutes="Minutes from now", message="Reminder message")
    async def remind_command(
        interaction: discord.Interaction, minutes: float, message: str
    ):
        if minutes <= 0:
            await interaction.response.send_message("❌ Minutes must be greater than 0.", ephemeral=True)
            return

        delay_seconds = minutes * 60
        reminders.add_reminder(
            channel_id=interaction.channel_id,
            user_id=interaction.user.id,
            message=message,
            delay_seconds=delay_seconds,
        )
        await interaction.response.send_message(
            f"⏰ Reminder set! I will ping you in **{minutes} minutes**: *\"{message}\"*",
            ephemeral=False,
        )

    @tree.command(name="gmail", description="Check latest unread emails from Gmail")
    async def gmail_command(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            from utils.google_integrations import fetch_important_emails
            emails = await asyncio.get_event_loop().run_in_executor(None, fetch_important_emails, 5)
            if not emails:
                await interaction.followup.send("📭 No unread emails found in your Gmail inbox.")
                return

            msg = "📧 **Latest Unread Gmail Inbox**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for i, email in enumerate(emails, 1):
                msg += (
                    f"\n**{i}. {email['subject']}**\n"
                    f"👤 From: `{email['from']}`\n"
                    f"📝 *{email['snippet'][:150]}...*\n"
                    f"─────────────────\n"
                )
            await interaction.followup.send(msg[:1950])
        except Exception as e:
            await interaction.followup.send(f"❌ Gmail Error: {str(e)}")

    @tree.command(name="calendar", description="Show today's Google Calendar events")
    async def calendar_command(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            from utils.google_integrations import fetch_todays_events
            from datetime import datetime
            events = await asyncio.get_event_loop().run_in_executor(None, fetch_todays_events)
            if not events:
                await interaction.followup.send("📅 No events scheduled for today in your Google Calendar.")
                return

            msg = "📅 **Today's Google Calendar Events**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for event in events:
                start_str = event['start']
                try:
                    dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    start_str = dt.strftime("%I:%M %p")
                except:
                    pass
                meet = f"\n🔗 [Join Meeting]({event['meet_link']})" if event['meet_link'] else ""
                msg += f"\n🕒 **{start_str}** — {event['summary']}{meet}\n"

            await interaction.followup.send(msg[:1950])
        except Exception as e:
            await interaction.followup.send(f"❌ Calendar Error: {str(e)}")

    @tree.command(name="log_expense", description="Log an expense to Google Sheets")
    @app_commands.describe(
        category="Expense category (Food, Fuel, Bills, etc.)",
        description="What was the expense for?",
        amount="Amount in rupees (e.g. 450)"
    )
    async def log_expense_command(
        interaction: discord.Interaction,
        category: str,
        description: str,
        amount: str,
    ):
        if not GOOGLE_SHEETS_URL:
            await interaction.response.send_message(
                "❌ Google Sheets URL not configured. Add `GOOGLE_SHEETS_URL=<your-sheet-url>` in `.env` file.",
                ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        try:
            from utils.google_integrations import log_expense_to_sheet
            import time
            date_str = time.strftime("%d-%b-%Y")
            success = await asyncio.get_event_loop().run_in_executor(
                None, log_expense_to_sheet, GOOGLE_SHEETS_URL, date_str, category, description, amount
            )
            if success:
                await interaction.followup.send(
                    f"✅ **Expense Logged to Google Sheets!**\n"
                    f"• 📅 Date: `{date_str}`\n"
                    f"• 📂 Category: `{category}`\n"
                    f"• 📝 Description: `{description}`\n"
                    f"• 💰 Amount: `₹{amount}`"
                )
            else:
                await interaction.followup.send("❌ Failed to log expense to Google Sheets.")
        except Exception as e:
            await interaction.followup.send(f"❌ Sheets Error: {str(e)}")

    @tree.command(name="help", description="Show AI Agent capabilities and help")
    async def help_command(interaction: discord.Interaction):
        help_text = (
            "🌟 **Antigravity Multi-LLM AI Agent** 🌟\n\n"
            "**Slash Commands:**\n"
            "• `/briefing` - Live Daily Morning Briefing\n"
            "• `/gmail` - Check latest unread Gmail emails\n"
            "• `/calendar` - Show today's Google Calendar events\n"
            "• `/log_expense [category] [description] [amount]` - Log expense to Google Sheets\n"
            "• `/usage` - Visual AI Token usage graph & stats meter\n"
            "• `/setup_channels` - Auto-create 7 dedicated AI channels\n"
            "• `/model [gemini|gpt|deepseek]` - Switch active AI model\n"
            "• `/status` - Check current active model, tokens & latency\n"
            "• `/clear` - Reset conversation history memory\n"
            "• `/remind [minutes] [message]` - Set a scheduled ping reminder\n"
            "• `/help` - Show this help menu\n"
        )
        await interaction.response.send_message(help_text)
