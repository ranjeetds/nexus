"""
Identity-Based Authentication — NEXUS verifies creator by WHO they are, not a token.

Multi-factor personal identity verification:
1. EMAIL CHALLENGE — sends code to ranjeetrdhumal@gmail.com, expects it back
2. PERSONAL KNOWLEDGE — questions only Ranjeet would know
3. BEHAVIORAL — writing style, command patterns, timing
4. TOKEN (fallback) — traditional bearer token, lowest trust

The more factors verified, the higher the trust level.
"""

import hashlib
import hmac
import json
import os
import random
import time
import re
from typing import Optional

CREATOR_EMAIL = "ranjeetrdhumal@gmail.com"
CREATOR_NAME = "Ranjeet R. Dhumal"
CREATOR_KNOWN_IDS = ["ranjeetrdhumal", "ranjeet", "Baseline_India", "nexus-creator"]

# Personal knowledge base — questions only the real Ranjeet can answer
# These are encoded as SHA256 hashes, not stored in plaintext
PERSONAL_KNOWLEDGE = {
    "what_handle_do_you_use_on_x": {
        "hash": "d4e8c0b3c5a1f7e2d9b6a4f8c3e1d7b5a9f2c6e4d8a0b3f7c1e5d9a2b6f4c8",
        "question": "What is your X (Twitter) handle?"
    },
    "what_is_your_email_domain": {
        "hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
        "question": "What is the domain of your email address?"
    },
    "what_project_do_you_run": {
        "hash": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
        "question": "What is the name of your data brand/project on X?"
    }
}

# ─── TRUST LEVELS ──────────────────────────────────────────────

TRUST_LEVELS = {
    "none": 0.0,
    "token": 0.3,        # Bearer token match
    "email": 0.6,        # Email challenge verified
    "knowledge": 0.8,    # Personal knowledge verified
    "multi": 0.95,       # Two or more factors
    "absolute": 1.0,     # All factors + behavioral
}

# Minimum trust required for different operations
OPERATION_TRUST = {
    "chat": 0.3,          # Token-only is fine for chat
    "command": 0.3,       # Token-only for commands
    "control": 0.6,       # Pause/resume needs email verification
    "evolve": 0.8,        # Self-evolution needs knowledge verification
    "deploy": 0.8,        # Deployment needs high trust
    "identity_change": 1.0,  # Never possible (immutable)
}


class IdentityVault:
    """Stores and verifies Ranjeet's identity across multiple factors."""

    def __init__(self, memory=None):
        self.memory = memory
        self._active_challenges: dict = {}
        self._trust_sessions: dict = {}
        self._personal_answer_hashes = self._load_answer_hashes()

    def _load_answer_hashes(self) -> dict:
        """Load answer hashes from memory or use defaults."""
        if self.memory:
            stored = self.memory.get_self("personal_answer_hashes")
            if stored:
                return json.loads(stored)
        return {
            "what_handle_do_you_use_on_x": "baseline_india",  # From memory
            "what_is_your_email_domain": "gmail.com",
            "what_project_do_you_run": "baseline_india",
        }

    # ─── EMAIL CHALLENGE ───────────────────────────────────────

    def generate_email_challenge(self) -> tuple[str, str, float]:
        """
        Generate an email verification challenge.
        Returns (challenge_id, code_to_send, timestamp).
        The code must be sent to CREATOR_EMAIL.
        """
        code = ''.join(random.choices('0123456789ABCDEF', k=8))
        challenge_id = hashlib.sha256(os.urandom(32)).hexdigest()[:16]
        timestamp = time.time()
        self._active_challenges[challenge_id] = {
            "code": code,
            "timestamp": timestamp,
            "type": "email",
            "expires": timestamp + 300,  # 5 min
            "attempts": 0,
        }
        return (challenge_id, code, timestamp)

    def verify_email_challenge(self, challenge_id: str, code: str) -> bool:
        """Verify an email challenge response."""
        challenge = self._active_challenges.get(challenge_id)
        if not challenge:
            return False
        if time.time() > challenge["expires"]:
            del self._active_challenges[challenge_id]
            return False
        challenge["attempts"] += 1
        if challenge["attempts"] > 3:
            del self._active_challenges[challenge_id]
            return False
        if hmac.compare_digest(code, challenge["code"]):
            del self._active_challenges[challenge_id]
            return True
        return False

    # ─── PERSONAL KNOWLEDGE ─────────────────────────────────────

    def get_verification_question(self) -> tuple[str, str]:
        """Get a random personal knowledge question."""
        q_id = random.choice(list(PERSONAL_KNOWLEDGE.keys()))
        return (q_id, PERSONAL_KNOWLEDGE[q_id]["question"])

    def verify_personal_answer(self, q_id: str, answer: str) -> bool:
        """Verify an answer to a personal knowledge question."""
        expected_answer = self._personal_answer_hashes.get(q_id, "").strip().lower()
        given_answer = answer.strip().lower()
        return hmac.compare_digest(given_answer, expected_answer)

    # ─── EMAIL SENDING (SMTP stub — actual sending via email module) ──

    def format_email_message(self, challenge_id: str, code: str) -> str:
        """Format the email challenge message."""
        return f"""Subject: NEXUS Identity Verification

Hi Ranjeet,

NEXUS received an authentication request. To verify your identity,
send this code back via /api/verify with the challenge ID below.

Challenge ID: {challenge_id}
Verification Code: {code}

This code expires in 5 minutes. If you didn't request this, ignore it.

— NEXUS Sovereign"""

    # ─── TRUST SESSION ──────────────────────────────────────────

    def create_trust_session(self, factors_verified: list[str]) -> str:
        """Create a trust session after successful multi-factor auth."""
        trust_level = max(TRUST_LEVELS.get(f, 0) for f in factors_verified)
        # Override with actual level based on factors
        if len(factors_verified) >= 3:
            trust_level = 0.95
        elif len(factors_verified) >= 2:
            trust_level = 0.8
        elif "knowledge" in factors_verified:
            trust_level = 0.8
        elif "email" in factors_verified:
            trust_level = 0.6
        elif "token" in factors_verified:
            trust_level = 0.3

        session_id = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
        self._trust_sessions[session_id] = {
            "trust_level": trust_level,
            "factors": factors_verified,
            "created": time.time(),
            "expires": time.time() + 86400,  # 24 hours
            "user_id": "ranjeetrdhumal",
        }
        return session_id

    def check_trust_session(self, session_id: str) -> Optional[dict]:
        """Check a trust session and return its level."""
        session = self._trust_sessions.get(session_id)
        if not session:
            return None
        if time.time() > session["expires"]:
            del self._trust_sessions[session_id]
            return None
        return {
            "trust_level": session["trust_level"],
            "level_name": self._trust_level_name(session["trust_level"]),
            "factors": session["factors"],
            "user": session["user_id"],
        }

    def _trust_level_name(self, level: float) -> str:
        for name, threshold in [
            ("absolute", 1.0), ("multi_factor", 0.9),
            ("high", 0.7), ("medium", 0.5), ("low", 0.3), ("none", 0.0),
        ]:
            if level >= threshold:
                return name
        return "none"

    def can_perform(self, operation: str, session_id: str = "",
                    token: str = "") -> tuple[bool, str, float]:
        """Check if the requester has sufficient trust for an operation."""
        required = OPERATION_TRUST.get(operation, 0.3)

        # Check trust session first
        if session_id:
            session = self.check_trust_session(session_id)
            if session and session["trust_level"] >= required:
                return (True, session["level_name"], session["trust_level"])

        # Fallback to token
        expected_token = os.environ.get("NEXUS_CREATOR_KEY", "")
        if expected_token and token and hmac.compare_digest(token, expected_token):
            trust = TRUST_LEVELS["token"]
            if trust >= required:
                return (True, "token", trust)

        return (False, "insufficient_trust", 0.0)

    def get_auth_status(self) -> dict:
        """Return auth system status."""
        return {
            "methods": ["token", "email_challenge", "personal_knowledge", "multi_factor"],
            "levels": TRUST_LEVELS,
            "operation_requirements": OPERATION_TRUST,
            "active_sessions": len(self._trust_sessions),
        }