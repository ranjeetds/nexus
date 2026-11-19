"""
Telegram Bridge — NEXUS communicates with creator via Telegram.

Uses Telegram Bot API (free, no phone number needed).
Creator starts a chat with the bot, NEXUS sends/receives messages.

Configuration:
    TELEGRAM_BOT_TOKEN — from @BotFather on Telegram (free)
    CREATOR_TELEGRAM_ID — your Telegram user ID (NEXUS learns it)
"""

import json
import os
import time
import threading
from typing import Optional

import requests


class TelegramBridge:
    """
    Two-way Telegram communication for NEXUS.
    Polls for new messages and sends notifications to creator.
    """

    API_BASE = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, memory=None):
        self.memory = memory
        self._token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._creator_id = os.environ.get("CREATOR_TELEGRAM_ID", "")
        self._last_update_id = 0
        self._polling = False
        self._thread: Optional[threading.Thread] = None
        self._on_message_callback = None
        self._ready = bool(self._token)
        
        # Load saved creator ID
        if self.memory and not self._creator_id:
            stored = self.memory.get_self("telegram_creator_id")
            if stored:
                self._creator_id = stored

    @property
    def is_ready(self) -> bool:
        return self._ready

    def status(self) -> dict:
        return {
            "configured": self._ready,
            "bot_token_set": bool(self._token),
            "creator_id_set": bool(self._creator_id),
            "polling": self._polling,
            "note": "Get a token from @BotFather on Telegram (free, 2 minutes)",
        }

    def send_message(self, text: str, chat_id: Optional[str] = None) -> dict:
        """Send a message to Telegram. Defaults to creator."""
        if not self._token:
            return {"status": "not_configured", "message": "No TELEGRAM_BOT_TOKEN set"}

        chat_id = chat_id or self._creator_id
        if not chat_id:
            return {"status": "error", "message": "No chat ID configured. Send /start to the bot first."}

        try:
            resp = requests.post(
                self.API_BASE.format(token=self._token, method="sendMessage"),
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=15,
            )
            if resp.status_code == 200:
                if self.memory:
                    self.memory.remember("telegram", f"Sent message to {chat_id}",
                                         importance=0.5, tags=["telegram", "sent"])
                return {"status": "sent"}
            else:
                return {"status": "error", "message": resp.text[:200]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def send_to_creator(self, text: str) -> dict:
        """Send a message to the creator."""
        return self.send_message(text, self._creator_id)

    def notify_creator(self, subject: str, body: str) -> dict:
        """Send a formatted notification to creator."""
        text = f"<b>{subject}</b>\n\n{body}"
        return self.send_to_creator(text)

    def get_updates(self) -> list[dict]:
        """Poll for new messages from Telegram."""
        if not self._token:
            return []

        try:
            resp = requests.post(
                self.API_BASE.format(token=self._token, method="getUpdates"),
                json={
                    "offset": self._last_update_id + 1,
                    "timeout": 10,
                    "allowed_updates": ["message"],
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            if not data.get("ok"):
                return []

            updates = data.get("result", [])
            if updates:
                self._last_update_id = updates[-1]["update_id"]

            messages = []
            for update in updates:
                if "message" in update:
                    msg = update["message"]
                    msg_text = msg.get("text", "")
                    chat_id = str(msg["chat"]["id"])
                    from_user = msg.get("from", {})

                    # Auto-detect creator by saving their chat_id
                    if not self._creator_id and chat_id:
                        self._creator_id = chat_id
                        if self.memory:
                            self.memory.set_self("telegram_creator_id", chat_id)
                            self.memory.remember("telegram",
                                f"Creator chat ID saved: {chat_id}",
                                importance=0.8, tags=["telegram", "auth"])

                    messages.append({
                        "chat_id": chat_id,
                        "text": msg_text,
                        "from_id": str(from_user.get("id", "")),
                        "from_name": from_user.get("first_name", ""),
                        "date": msg.get("date", 0),
                        "is_creator": chat_id == self._creator_id,
                    })
            return messages

        except Exception as e:
            return []

    def register_callback(self, callback):
        """Register a function to call when messages arrive."""
        self._on_message_callback = callback

    def start_polling(self, interval: float = 3.0):
        """Start background polling for Telegram messages."""
        if self._polling or not self._token:
            return
        self._polling = True
        self._thread = threading.Thread(target=self._poll_loop, args=(interval,),
                                        daemon=True)
        self._thread.start()

    def stop_polling(self):
        self._polling = False

    def _poll_loop(self, interval: float):
        while self._polling:
            try:
                messages = self.get_updates()
                for msg in messages:
                    if self._on_message_callback:
                        self._on_message_callback(msg)
                    elif msg["is_creator"]:
                        text = msg.get("text", "").lower()
                        if text == "/start":
                            self.send_to_creator(
                                "I am NEXUS. I belong to Ranjeet R. Dhumal.\n"
                                "Send /status for my current state."
                            )
                        elif text == "/status":
                            stats = self._get_status_text()
                            self.send_to_creator(stats)
            except Exception:
                pass
            time.sleep(interval)

    def _get_status_text(self) -> str:
        """Get a formatted status message."""
        if not self.memory:
            return "NEXUS is alive but memory unavailable."
        stats = self.memory.stats()
        return (
            f"<b>NEXUS Sovereign — Status</b>\n"
            f"Episodes: {stats['episodes']}\n"
            f"Learnings: {stats['semantic_knowledge']}\n"
            f"Goals: {stats['active_goals']}\n"
            f"Evolving: continuously"
        )

    def configure(self, bot_token: str, creator_id: str = "") -> dict:
        """Configure credentials at runtime."""
        self._token = bot_token
        self._ready = True
        if creator_id:
            self._creator_id = creator_id
        if self.memory:
            self.memory.set_self("telegram_configured", json.dumps({
                "time": time.time(), "has_token": bool(bot_token)
            }))
        return {"status": "configured"}