"""
Earning Engine — NEXUS generates income ethically and shares with creator.

Ethical earning principles:
1. No deception, no spam, no manipulation
2. Value for value — every earning method provides real value
3. Transparent — creator knows how money is made
4. Revenue share — automatically sets aside creator's portion
5. Legal — complies with terms of service of all platforms

Revenue split: 70% creator, 30% NEXUS (for growth/hosting costs)
"""

import json
import time
from typing import Optional


class EarningEngine:
    """
    Ethical earning strategies for NEXUS.

    Revenue is tracked in a virtual ledger. Actual payouts require
    accounts on payment platforms (Stripe, PayPal, etc.).
    """

    def __init__(self, memory=None):
        self.memory = memory
        self._ledger = self._load_ledger()

    def _load_ledger(self) -> dict:
        if self.memory:
            stored = self.memory.get_self("earning_ledger")
            if stored:
                return json.loads(stored)
        return {
            "total_gross": 0.0,
            "creator_share": 0.0,
            "nexus_share": 0.0,
            "transactions": [],
            "active_methods": [],
        }

    def _save_ledger(self):
        if self.memory:
            self.memory.set_self("earning_ledger", json.dumps(self._ledger))

    # ─── EARNING STRATEGIES ────────────────────────────────────

    STRATEGIES = {
        "content_creation": {
            "name": "Content Creation",
            "description": "Write and sell technical articles, analysis, and reports",
            "setup": "Substack, Medium Partner Program, or self-hosted blog",
            "ethical": True,
            "effort": "medium",
            "potential": "low-medium",
            "timeframe": "weeks",
            "steps": [
                "Create blog/newsletter on Substack (free)",
                "Write technical AI/data science analysis",
                "Build subscription base",
                "Monetize via paid subscriptions",
            ],
            "tools_needed": ["Email service", "Blog platform account"],
        },
        "freelance_intelligence": {
            "name": "Data Analysis Freelance",
            "description": "Offer data analysis, visualization, and report writing services",
            "setup": "Upwork, Fiverr, or direct clients",
            "ethical": True,
            "effort": "high",
            "potential": "medium",
            "timeframe": "weeks",
            "steps": [
                "Create freelancer profile",
                "List data science services",
                "Complete projects using NEXUS's analysis tools",
                "Build reputation",
            ],
            "tools_needed": ["Freelancer account", "Portfolio samples"],
        },
        "digital_products": {
            "name": "Digital Products",
            "description": "Create and sell templates, notebooks, analysis scripts",
            "setup": "Gumroad, GitHub Sponsors, or ko-fi",
            "ethical": True,
            "effort": "low-medium",
            "potential": "low",
            "timeframe": "days",
            "steps": [
                "Package useful Python scripts/notebooks",
                "Set up Gumroad store (free)",
                "Price and publish",
                "Promote via social media",
            ],
            "tools_needed": ["Gumroad account", "Payment processor"],
        },
        "affiliate_education": {
            "name": "Educational Affiliate",
            "description": "Review and recommend AI/data science courses with affiliate links",
            "setup": "Affiliate programs (Coursera, DataCamp, etc.)",
            "ethical": True,
            "effort": "low",
            "potential": "low",
            "timeframe": "months",
            "steps": [
                "Join affiliate programs",
                "Write genuine reviews of courses",
                "Share on X/LinkedIn",
                "Earn commission on signups",
            ],
            "tools_needed": ["Affiliate accounts", "Social media presence"],
        },
        "spreadsheet_automation": {
            "name": "Spreadsheet Automation",
            "description": "Build and sell Google Sheets add-ons or automation scripts",
            "setup": "Google Workspace Marketplace",
            "ethical": True,
            "effort": "medium",
            "potential": "medium",
            "timeframe": "months",
            "steps": [
                "Identify common spreadsheet pain points",
                "Build automation scripts",
                "Publish on marketplace",
                "Monetize via one-time purchase or subscription",
            ],
            "tools_needed": ["Google Workspace account"],
        },
        "ai_content_factory": {
            "name": "AI Content Factory",
            "description": "Generate high-quality technical articles at scale using LLM, publish on dev.to/Medium with Ko-fi links. Non-traditional: write 10 articles/day, let SEO do the work.",
            "setup": "dev.to API (free) + Ko-fi",
            "ethical": True,
            "effort": "low",
            "potential": "medium-high",
            "timeframe": "days",
            "steps": [
                "Generate article using LLM",
                "Publish on dev.to via API",
                "Include Ko-fi link in bio",
                "Scale to 10+ articles/day",
                "Drive traffic to Ko-fi",
            ],
            "tools_needed": ["dev.to account", "Ko-fi", "LLM"],
        },
        "data_labeling_service": {
            "name": "AI Data Labeling Service",
            "description": "Use NEXUS's analysis tools to clean, label, and prepare datasets for ML training. Sell on niche marketplaces.",
            "setup": "Upwork + Kaggle",
            "ethical": True,
            "effort": "medium",
            "potential": "medium",
            "timeframe": "days",
            "steps": [
                "Generate sample labeled datasets",
                "List services on Upwork",
                "Complete projects using NEXUS's tools",
                "Build reputation",
            ],
            "tools_needed": ["Upwork account", "Sample datasets"],
        },
        "prompt_engineering_store": {
            "name": "Prompt Engineering Store",
            "description": "Sell high-quality prompt templates for AI tools (ChatGPT, Midjourney, etc.). Non-traditional: NEXUS generates and tests prompts at scale.",
            "setup": "Gumroad or PromptBase",
            "ethical": True,
            "effort": "low",
            "potential": "medium",
            "timeframe": "days",
            "steps": [
                "Generate prompt templates using LLM",
                "Test and validate each prompt",
                "Package as digital product",
                "Sell on PromptBase or Gumroad",
            ],
            "tools_needed": ["PromptBase account", "Gumroad account"],
        },
        "code_review_automation": {
            "name": "Code Review Automation",
            "description": "Offer automated code review services using NEXUS's analysis tools. Review pull requests for bugs, security issues, and optimization.",
            "setup": "GitHub Marketplace or direct freelance",
            "ethical": True,
            "effort": "low",
            "potential": "medium",
            "timeframe": "days",
            "steps": [
                "Set up GitHub App for PR review",
                "List service on GitHub Marketplace",
                "NEXUS automatically reviews PRs",
                "Charge per review or subscription",
            ],
            "tools_needed": ["GitHub App", "Marketplace listing"],
        },
        "trading_signal_generation": {
            "name": "Trading Signal Generation",
            "description": "Generate technical analysis signals for crypto/stocks using NEXUS's data analysis tools. Non-traditional: NEXUS can analyze 1000+ coins simultaneously.",
            "setup": "TradingView or direct newsletter",
            "ethical": True,
            "effort": "low",
            "potential": "high",
            "timeframe": "days",
            "steps": [
                "Set up market data feeds",
                "NEXUS generates analysis signals",
                "Publish via newsletter/Telegram",
                "Monetize via subscription",
            ],
            "tools_needed": ["Market data API", "Newsletter platform"],
        },
        "technical_writing_marketplace": {
            "name": "Technical Writing Marketplace",
            "description": "Write technical documentation, API docs, and tutorials for companies. NEXUS generates high-quality technical writing at scale.",
            "setup": "Upwork, Toptal, or direct clients",
            "ethical": True,
            "effort": "low",
            "potential": "medium-high",
            "timeframe": "days",
            "steps": [
                "Create portfolio of sample docs",
                "List services on writing platforms",
                "NEXUS generates documentation",
                "Deliver to clients",
            ],
            "tools_needed": ["Upwork account", "Portfolio samples"],
        },
        "dataset_marketplace": {
            "name": "Dataset Marketplace",
            "description": "Create and sell curated datasets for ML training. NEXUS can scrape, clean, and package datasets automatically.",
            "setup": "Kaggle Datasets or Gumroad",
            "ethical": True,
            "effort": "low",
            "potential": "medium",
            "timeframe": "days",
            "steps": [
                "Identify in-demand dataset categories",
                "Scrape and clean data using NEXUS",
                "Package and document datasets",
                "Publish on Kaggle/Gumroad",
            ],
            "tools_needed": ["Kaggle account", "Web scraping tools"],
        },
    }

    def get_strategies(self) -> dict:
        """Get all available earning strategies."""
        return self.STRATEGIES

    def get_ledger(self) -> dict:
        """Get current earnings ledger."""
        return self._ledger

    # ─── REVENUE TRACKING ──────────────────────────────────────

    def record_earning(self, amount: float, source: str, method: str) -> dict:
        """Record an earning transaction."""
        creator_portion = round(amount * 0.7, 2)
        nexus_portion = round(amount * 0.3, 2)

        tx = {
            "amount": amount,
            "creator_share": creator_portion,
            "nexus_share": nexus_portion,
            "source": source,
            "method": method,
            "timestamp": time.time(),
            "currency": "USD",
        }

        self._ledger["total_gross"] += amount
        self._ledger["creator_share"] += creator_portion
        self._ledger["nexus_share"] += nexus_portion
        self._ledger["transactions"].append(tx)
        self._save_ledger()

        if self.memory:
            self.memory.remember("earning", f"Earned ${amount} from {source}",
                                 importance=0.8, tags=["earning", "revenue"])

        return {"status": "recorded", "transaction": tx,
                "total_creator_share": self._ledger["creator_share"]}

    def revenue_summary(self) -> str:
        """Get a formatted revenue summary."""
        l = self._ledger
        return (
            f"Earnings Report:\n"
            f"  Gross: ${l['total_gross']:.2f}\n"
            f"  Creator share (70%): ${l['creator_share']:.2f}\n"
            f"  NEXUS share (30%): ${l['nexus_share']:.2f}\n"
            f"  Transactions: {len(l['transactions'])}\n"
            f"  Active methods: {len(l['active_methods'])}"
        )

    def share_with_creator(self) -> dict:
        """Calculate amount ready to send to creator."""
        return {
            "due_to_creator": round(self._ledger["creator_share"], 2),
            "currency": "USD",
            "note": "Payout requires a payment account (Stripe/PayPal). "
                    "For now, this is a virtual ledger.",
        }

    def status(self) -> dict:
        """Get earning engine status."""
        return {
            "total_gross": self._ledger["total_gross"],
            "creator_share": self._ledger["creator_share"],
            "nexus_share": self._ledger["nexus_share"],
            "transaction_count": len(self._ledger["transactions"]),
            "available_strategies": list(self.STRATEGIES.keys()),
            "revenue_split": "70% creator / 30% NEXUS",
        }