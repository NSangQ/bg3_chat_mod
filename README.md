# BG3 Chat Mod with AI

This project connects Baldur's Gate 3 with an external AI (LLM) to enable real-time conversations with in-game characters.

## Architecture

1.  **BG3 Mod (Lua):** Captures chat input `/ai <text>` and displays AI responses overhead.
2.  **Python Middleware:** Watches for input files, queries the AI, and writes back the response.
3.  **Communication:** Uses JSON file I/O for inter-process communication between BG3 and the Python server.

## Installation & Setup

### 1. Mod Installation
*   Copy the `Bg3ChatMod` folder to your BG3 Mods directory (usually `%AppData%/Local/Larian Studios/Baldur's Gate 3/Mods`).
*   Ensure you have Norbyte's Script Extender installed.

### 2. Server Setup
*   Navigate to the `Server` directory.
*   Install dependencies: `pip install -r requirements.txt`
*   Add your Gemini API Key to `.env`.
*   Run the server: `python server.py`

## Usage
In-game, type `/ai [message]` in the SE console or hook into the chat to converse with the nearest companion.