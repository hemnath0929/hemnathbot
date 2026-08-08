# 📖 User Manual: Hemnath Personal AI Agent (`hemnath_bot`)

Welcome to your **Multi-LLM Personal AI Agent**! This manual will guide you through using all the channels, slash commands, features, and shortcuts available in your Discord server.

---

## 🚀 1. Quick Start Guide

1. Open your Discord Server (**`Hemnathbot`**).
2. You will see 7 dedicated text channels created on the left sidebar.
3. Simply click any channel and start chatting with the bot or type slash commands (e.g., `/help`, `/briefing`, `/usage`).

---

## 📂 2. Dedicated Channels Guide

Each channel is optimized with custom AI personas and default models:

### 💬 `#general-ai`
- **Purpose**: General QA, quick doubts, daily chat, and casual brainstorming.
- **Model**: **Gemini 2.5 Flash** (Ultra fast).
- **How to use**: Type any question normally.

### 💻 `#code-lab`
- **Purpose**: Programming, bug fixing, script generation, and algorithms.
- **Model**: **DeepSeek-R1 / DeepSeek-V3** (Senior Coder Persona).
- **How to use**: Ask coding questions or paste code snippets to get refactored code blocks with explanations.

### ⏰ `#reminders-and-tasks`
- **Purpose**: Scheduling alarms, reminders, and receiving Daily Morning Briefings.
- **Model**: Natural Language Reminder Parser + Gemini.
- **How to use**: 
  - Type natural text: *"Remind me in 15 minutes to check email"* or *"Remind me at 6:30 PM to go to gym"*.
  - Receive the **Daily 8:00 AM Morning Briefing** automatically every morning!

### 🔍 `#web-research`
- **Purpose**: Live web search synthesis and article link summaries.
- **Model**: Gemini + Search integration.
- **How to use**: Paste a link or ask *"Search web for latest AI news"*.

### 💰 `#expense-tracker`
- **Purpose**: Financial logging and bill calculation.
- **Model**: Financial Parser.
- **How to use**: Type *"Spent ₹350 on petrol"* or upload a photo of a bill receipt.

### 🧠 `#second-brain`
- **Purpose**: Permanent notes, passwords, ideas, and knowledge store.
- **Model**: Memory Retriever.
- **How to use**: Save important info or ask *"What did I save about my vehicle details?"*.

### 🖼️ `#image-studio`
- **Purpose**: Image analysis, document text extraction (OCR), and PDF reading.
- **Model**: Gemini Vision.
- **How to use**: Attach an image or screenshot to your message.

---

## ⚡ 3. Slash Commands Reference

Type `/` in Discord chat to bring up the command menu:

| Command | Syntax | Description |
| :--- | :--- | :--- |
| **`/briefing`** | `/briefing` | Generates a live **Daily Morning Briefing** card (Weather, Tech News, Pending Reminders, Productivity Tip). |
| **`/usage`** | `/usage` | Generates a text meter + **Visual Matplotlib Bar Graph PNG** of your AI token usage. |
| **`/status`** | `/status` | Displays current active model, bot latency (ms), and total tokens used. |
| **`/model`** | `/model provider:[gemini\|gpt\|deepseek]` | Switches the active AI provider for the current channel. |
| **`/remind`** | `/remind minutes:[N] message:[text]` | Sets a timer reminder for N minutes. |
| **`/setup_channels`** | `/setup_channels` | Auto-creates all 7 dedicated channels in your server if missing. |
| **`/clear`** | `/clear` | Clears short-term conversation context memory for the channel. |
| **`/help`** | `/help` | Shows the slash commands help menu. |

---

## ⏰ 4. Natural Language Reminders & Scheduling

In `#reminders-and-tasks` (or `#general-ai`), you can schedule reminders in plain language without any slash commands:

### Examples:
- `"Remind me in 30 minutes to drink water"`
- `"Remind me at 5:30 PM to join meeting"`
- `"Schedule a reminder tomorrow at 9 AM to pay electricity bill"`

**Bot Response**:
The bot will return a confirmation card:
> ⏰ **Reminder Scheduled Successfully!**
> • **Time:** `In 30 minutes`
> • **Task:** *"drink water"*

When the timer arrives, `hemnath_bot` will ping you directly: **`🔔 @Devil0329 Reminder Alert: drink water`**.

---

## 🖼️ 5. Uploading Images & Files

1. Drag and drop or attach an image (PNG, JPG, WebP) in Discord chat.
2. Add an optional prompt (e.g. *"Explain this error code"* or *"Extract text from this image"*).
3. If no prompt is provided, the bot automatically analyzes and describes the image.

---

## 🛠️ 6. Running and Managing the Bot

The bot runs locally in your project folder `d:\personal project\hemnath personal agent`.

### Start the Bot:
Open terminal in the project directory and run:
```bash
.\.venv\Scripts\python.exe main.py
```

### Stop the Bot:
Press `Ctrl + C` in the terminal.

---
*Happy Productivity with Antigravity AI Agent!* 🚀
