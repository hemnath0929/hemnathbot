import sqlite3
import time
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = "token_usage.db"

class TokenTracker:
    """Tracks LLM token usage per provider and generates visual matplotlib charts."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS token_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                provider TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                channel_id INTEGER NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def log_usage(
        self,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        channel_id: int,
    ):
        total = prompt_tokens + completion_tokens
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO token_logs (timestamp, provider, prompt_tokens, completion_tokens, total_tokens, channel_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (time.time(), provider.lower(), prompt_tokens, completion_tokens, total, channel_id),
        )
        conn.commit()
        conn.close()

    def get_summary(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total tokens by provider
        cursor.execute("SELECT provider, SUM(total_tokens), COUNT(*) FROM token_logs GROUP BY provider")
        rows = cursor.fetchall()
        
        # Overall total
        cursor.execute("SELECT SUM(total_tokens) FROM token_logs")
        overall = cursor.fetchone()[0] or 0
        
        conn.close()

        provider_stats = {r[0]: {"tokens": r[1], "requests": r[2]} for r in rows}
        return {
            "overall_total": overall,
            "providers": provider_stats,
        }

    def generate_usage_chart(self, output_path: str = "token_chart.png") -> str:
        """Generates a dark-themed visual bar chart using matplotlib."""
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        summary = self.get_summary()
        providers_data = summary["providers"]

        providers = ["gemini", "gpt", "deepseek"]
        tokens = [providers_data.get(p, {}).get("tokens", 0) for p in providers]
        colors = ["#4285F4", "#10A37F", "#4F46E5"]

        # Create plot
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(7, 3.5), dpi=150)

        bars = ax.barh(providers, tokens, color=colors, height=0.5)
        ax.set_title("AI Model Token Consumption Summary", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Total Tokens Used", fontsize=10)
        ax.grid(axis="x", linestyle="--", alpha=0.3)

        # Add values on bars
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + (max(tokens) * 0.02 if max(tokens) > 0 else 10),
                bar.get_y() + bar.get_height() / 2,
                f"{width:,} tokens",
                va="center",
                ha="left",
                fontsize=9,
                color="white",
            )

        plt.tight_layout()
        fig.savefig(output_path, bbox_inches="tight", transparent=False)
        plt.close(fig)
        return output_path
