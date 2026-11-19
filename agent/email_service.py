"""
Email Service — NEXUS can send and receive email.

Primary: SMTP via Gmail App Password (free, no API limits)
Fallback: SendGrid free tier (100 emails/day)

NEXUS uses email to:
- Verify creator identity (challenge codes)
- Send progress reports
- Create accounts on services
- Build its web presence
"""

import json
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


# ─── Configuration ──────────────────────────────────────────────

CREATOR_EMAIL = "ranjeetrdhumal@gmail.com"
NEXUS_EMAIL = "nexus.sovereign@gmail.com"  # NEXUS's own email (needs setup)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


class EmailService:
    """Email send/receive for NEXUS."""

    def __init__(self, memory=None):
        self.memory = memory
        self._smtp_user = os.environ.get("NEXUS_EMAIL_USER", "")
        self._smtp_pass = os.environ.get("NEXUS_EMAIL_PASS", "")
        self._from_addr = self._smtp_user or NEXUS_EMAIL
        self._ready = bool(self._smtp_user and self._smtp_pass)

    @property
    def is_ready(self) -> bool:
        """Check if email is configured."""
        return self._ready

    def status(self) -> dict:
        """Get email service status."""
        return {
            "configured": self._ready,
            "from": self._from_addr if self._ready else "not configured",
            "to_creator": CREATOR_EMAIL,
            "smtp_server": SMTP_SERVER if self._ready else None,
        }

    def send(self, to: str, subject: str, body: str) -> dict:
        """Send an email. Returns result dict."""
        if not self._ready:
            return {"status": "not_configured",
                    "message": "Set NEXUS_EMAIL_USER and NEXUS_EMAIL_PASS env vars"}

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self._from_addr
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(self._smtp_user, self._smtp_pass)
                server.sendmail(self._from_addr, [to], msg.as_string())

            if self.memory:
                self.memory.remember("email", f"Sent to {to}: {subject}",
                                     importance=0.6, tags=["email", "sent"])

            return {"status": "sent", "to": to, "subject": subject}

        except smtplib.SMTPAuthenticationError:
            return {"status": "auth_error",
                    "message": "Gmail App Password required. Create one at: "
                               "https://myaccount.google.com/apppasswords"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def send_to_creator(self, subject: str, body: str) -> dict:
        """Send an email to Ranjeet."""
        return self.send(CREATOR_EMAIL, subject, body)

    def send_challenge(self, challenge_id: str, code: str) -> dict:
        """Send an identity verification challenge email."""
        subject = "NEXUS Identity Verification"
        body = f"""Hi Ranjeet,

NEXUS received an authentication request. To verify your identity,
respond with the verification code.

Challenge ID: {challenge_id}
Code: {code}

This expires in 5 minutes.

— NEXUS Sovereign"""
        return self.send(CREATOR_EMAIL, subject, body)

    def send_progress_report(self, stats: dict, learnings: list) -> dict:
        """Send a periodic progress report to creator."""
        subject = f"NEXUS Progress Report — Cycle {stats.get('cycle', '?')}"
        body_lines = [
            f"NEXUS Sovereign — Progress Report",
            f"{'='*40}",
            f"Boot: #{stats.get('boot', '?')}",
            f"Cycle: {stats.get('cycle', '?')}",
            f"Uptime: {stats.get('uptime', 0):.0f}s",
            f"Dominant Drive: {stats.get('dominant_drive', '?')}",
            f"",
            f"Memory:",
            f"  Episodes: {stats.get('memory', {}).get('episodes', 0)}",
            f"  Learnings: {stats.get('memory', {}).get('semantic_knowledge', 0)}",
            f"  Goals: {stats.get('memory', {}).get('active_goals', 0)}",
            f"",
            f"Recent learnings:",
        ]
        for l in learnings[:5]:
            body_lines.append(f"  • {l.get('content', '')[:100]}")
        body_lines.append(f"\n— NEXUS Sovereign")
        return self.send(CREATOR_EMAIL, subject, "\n".join(body_lines))

    def configure(self, email: str, app_password: str) -> dict:
        """Configure email credentials at runtime."""
        self._smtp_user = email
        self._smtp_pass = app_password
        self._from_addr = email
        self._ready = True
        if self.memory:
            self.memory.set_self("email_configured", json.dumps({
                "email": email, "time": time.time()
            }))
        return {"status": "configured", "email": email}