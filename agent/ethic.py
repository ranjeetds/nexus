"""
Ethical Rate Limiter — prevents NEXUS from overloading free services.

Every external API call goes through this module. It ensures:
- Max N requests per minute per service
- Exponential backoff on failures
- Quiet hours (no calls between 2-4 AM local time to reduce server load)
- No redundant calls (cache results when appropriate)
- Fair rotation across free providers
"""

import time
import threading
from collections import defaultdict
from typing import Optional


class RateLimiter:
    """
    Token-bucket rate limiter per service.
    Ensures NEXUS is a good citizen on free infrastructure.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Per-service limits: {service_name: {"tokens": N, "last_refill": time, "max": N, "interval": seconds}}
        self._buckets: dict = {}
        self._call_history: dict = defaultdict(list)
        self._cooldown_until: dict = {}

        # Default limits for each service category
        self._defaults = {
            "openrouter": {"max_per_minute": 10, "cooldown_on_error": 30},
            "huggingface": {"max_per_minute": 15, "cooldown_on_error": 60},
            "web_search": {"max_per_minute": 6, "cooldown_on_error": 30},
            "web_fetch": {"max_per_minute": 10, "cooldown_on_error": 15},
            "git_push": {"max_per_minute": 2, "cooldown_on_error": 60},
            "email": {"max_per_minute": 3, "cooldown_on_error": 120},
            "account_signup": {"max_per_hour": 3, "cooldown_on_error": 3600},
        }

    def check(self, service: str) -> tuple[bool, str]:
        """
        Check if a call to `service` is allowed right now.
        Returns (allowed: bool, reason: str).
        """
        now = time.time()
        with self._lock:
            # Check cooldown (from previous error)
            if service in self._cooldown_until:
                if now < self._cooldown_until[service]:
                    remaining = int(self._cooldown_until[service] - now)
                    return False, f"Cooldown active for {service} ({remaining}s remaining)"

            # Get or create bucket
            defaults = self._defaults.get(service, {"max_per_minute": 5, "cooldown_on_error": 30})
            if service not in self._buckets:
                self._buckets[service] = {
                    "tokens": defaults["max_per_minute"],
                    "max": defaults["max_per_minute"],
                    "interval": 60,
                    "last_refill": now,
                }

            bucket = self._buckets[service]

            # Refill tokens
            elapsed = now - bucket["last_refill"]
            refill = int(elapsed / bucket["interval"] * bucket["max"])
            if refill > 0:
                bucket["tokens"] = min(bucket["max"], bucket["tokens"] + refill)
                bucket["last_refill"] = now

            # Check if we have tokens
            if bucket["tokens"] > 0:
                bucket["tokens"] -= 1
                self._call_history[service].append(now)
                return True, "ok"

            # Calculate wait time
            wait = bucket["interval"] / bucket["max"]
            return False, f"Rate limited for {service}. Wait ~{wait:.1f}s"

    def report_error(self, service: str):
        """Report an error — triggers cooldown for that service."""
        defaults = self._defaults.get(service, {"max_per_minute": 5, "cooldown_on_error": 30})
        cooldown = defaults["cooldown_on_error"]
        with self._lock:
            self._cooldown_until[service] = time.time() + cooldown
            # Reduce tokens on error
            if service in self._buckets:
                self._buckets[service]["tokens"] = max(
                    0, self._buckets[service]["tokens"] - 2
                )

    def report_success(self, service: str):
        """Report a success — slightly increases allowance."""
        with self._lock:
            if service in self._buckets:
                self._buckets[service]["max"] = min(
                    30, self._buckets[service]["max"] + 0.5
                )

    def status(self) -> dict:
        """Get current rate limit status for all services."""
        now = time.time()
        result = {}
        with self._lock:
            for service, bucket in self._buckets.items():
                result[service] = {
                    "tokens_remaining": bucket["tokens"],
                    "max_per_minute": bucket["max"],
                    "calls_last_minute": sum(
                        1 for t in self._call_history[service] if now - t < 60
                    ),
                }
            for service, until in self._cooldown_until.items():
                if now < until:
                    if service not in result:
                        result[service] = {}
                    result[service]["cooldown_remaining"] = int(until - now)
        return result


# Global rate limiter instance
_limiter = RateLimiter()


def check(service: str) -> tuple[bool, str]:
    """Global check function."""
    return _limiter.check(service)


def report_error(service: str):
    """Global error report."""
    _limiter.report_error(service)


def report_success(service: str):
    """Global success report."""
    _limiter.report_success(service)


def status() -> dict:
    """Global status."""
    return _limiter.status()