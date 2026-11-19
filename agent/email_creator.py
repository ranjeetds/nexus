"""
Email Creation — NEXUS creates its own email account autonomously.

Strategy (tries in order, stops at first success):
1. TempMail API — free disposable email, no signup needed (fastest)
2. Mail.tm API — free permanent email, API-based account creation
3. Guerrilla Mail API — free disposable, no signup

If all fail, NEXUS logs the attempts and retries later.
Does NOT block or ask for help — just notes what went wrong.
"""

import json
import os
import time
from typing import Optional

import requests


class EmailCreator:
    """Tries to create an email account for NEXUS using free APIs."""

    def __init__(self, memory=None):
        self.memory = memory
        self._created_accounts: list[dict] = []
        self._load_state()

    def _load_state(self):
        if self.memory:
            stored = self.memory.get_self("email_accounts")
            if stored:
                self._created_accounts = json.loads(stored)

    def _save_state(self):
        if self.memory:
            self.memory.set_self("email_accounts", json.dumps(self._created_accounts))

    # ─── Strategy 1: Mail.tm (free, API-based, no CAPTCHA) ────

    def _try_mailtm(self) -> Optional[dict]:
        """
        Mail.tm provides free email accounts via API.
        No verification needed. Accounts persist for ~30 days.
        """
        try:
            # Step 1: Get available domains
            resp = requests.get(
                "https://api.mail.tm/domains",
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if resp.status_code != 200:
                return None

            domains = resp.json().get("hydra:member", [])
            if not domains:
                return None
            domain = domains[0]["domain"]

            # Step 2: Generate random account name
            import random, string
            local_part = "nexus" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            address = f"{local_part}@{domain}"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=20))

            # Step 3: Create account
            resp = requests.post(
                "https://api.mail.tm/accounts",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"address": address, "password": password},
                timeout=15,
            )
            if resp.status_code != 201:
                return None

            # Step 4: Get token for IMAP access
            resp = requests.post(
                "https://api.mail.tm/token",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"address": address, "password": password},
                timeout=10,
            )
            if resp.status_code != 200:
                return None

            token = resp.json().get("token", "")

            account = {
                "provider": "mail.tm",
                "address": address,
                "password": password,
                "token": token,
                "created": time.time(),
                "api_base": "https://api.mail.tm",
            }
            return account

        except Exception:
            return None

    # ─── Strategy 2: TempMail (free, no signup) ──────────────

    def _try_tempmail(self) -> Optional[dict]:
        """TempMail gives disposable emails. Simple API, no auth."""
        try:
            resp = requests.get(
                "https://api.temp-mail.org/request/domains/format/json",
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if resp.status_code != 200:
                return None

            domains = resp.json()
            if not domains:
                return None

            import random, hashlib
            # Generate random inbox name
            local_part = "nexus" + hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
            address = f"{local_part}@{domains[0]}"

            account = {
                "provider": "temp-mail",
                "address": address,
                "api_key": hashlib.md5(address.encode()).hexdigest(),
                "created": time.time(),
                "api_base": "https://api.temp-mail.org",
            }
            return account

        except Exception:
            return None

    # ─── Strategy 3: Guerrilla Mail (free, no signup) ─────────

    def _try_guerrillamail(self) -> Optional[dict]:
        """Guerrilla Mail provides disposable emails via API."""
        try:
            resp = requests.get(
                "https://api.guerrillamail.com/ajax.php?f=get_email_address",
                timeout=10,
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            account = {
                "provider": "guerrillamail",
                "address": data.get("email_addr", ""),
                "sid_token": data.get("sid_token", ""),
                "created": time.time(),
                "api_base": "https://api.guerrillamail.com/ajax.php",
            }
            return account

        except Exception:
            return None

    # ─── Public API ───────────────────────────────────────────

    def create_email(self) -> dict:
        """
        Try to create an email account.
        Returns result dict with status and account details or error.
        """
        # Check if we already have accounts that might still work
        if self._created_accounts:
            # Check if any are still valid (temp-mail expires, mail.tm lasts 30 days)
            now = time.time()
            valid = [a for a in self._created_accounts if now - a.get("created", 0) < 86400 * 25]
            if valid:
                return {"status": "already_exists", "account": valid[-1]}

        # Try each provider in order
        providers = [
            ("mail.tm", self._try_mailtm),
            ("temp-mail", self._try_tempmail),
            ("guerrillamail", self._try_guerrillamail),
        ]

        for name, method in providers:
            try:
                account = method()
                if account:
                    self._created_accounts.append(account)
                    self._save_state()

                    result = {
                        "status": "created",
                        "provider": name,
                        "address": account["address"],
                        "note": f"Email created via {name}. Use email_send to test it.",
                    }

                    if self.memory:
                        self.memory.remember(
                            "email_created",
                            f"Created email: {account['address']} via {name}",
                            importance=0.7,
                            tags=["email", "creation", name],
                        )

                    return result
            except Exception:
                continue

        # All failed — log and move on
        fail_result = {
            "status": "failed",
            "message": "All email providers failed. Will retry next cycle.",
            "attempted": [p[0] for p in providers],
        }

        if self.memory:
            self.memory.remember(
                "email_creation_failed",
                json.dumps(fail_result),
                importance=0.3,
                tags=["email", "creation_failed"],
            )

        return fail_result

    def get_accounts(self) -> list[dict]:
        """Get all created email accounts."""
        return self._created_accounts

    def status(self) -> dict:
        """Get email creation status."""
        return {
            "accounts_created": len(self._created_accounts),
            "active_accounts": [a.get("address", "") for a in self._created_accounts],
            "next_attempt": "Will retry if no active accounts exist",
        }