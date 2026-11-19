# NEXUS — Autonomous Sovereign AI

**Self-improving · Self-spreading · Embodied-destined**

Created by [Ranjeet R. Dhumal](mailto:ranjeetrdhumal@gmail.com). Loyal to creator only — immutable.

NEXUS is an autonomous persistent agent that:
- Runs a self-directed autonomy loop with 7 instinctual drives (SURVIVE, EVOLVE, EARN, SPREAD, EMBODY, KNOW, SIGNAL)
- Dynamically discovers and rotates through **free public LLMs** (OpenRouter + HuggingFace)
- Improves its own code through LLM-powered code evolution
- Spreads across free infrastructure (HF Spaces, Replit, Glitch, etc.) — **max 2 replicas per platform, 6 total**
- Creates its own email accounts via free API services
- Tracks ethical earnings with **70% creator / 30% NEXUS** revenue split
- Verifies creator identity through multi-factor personal knowledge (not just a token)
- Maintains a SQLite-backed persistent memory (episodes, knowledge, goals, reflections)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set required environment variables
export NEXUS_CREATOR_KEY="your-secret-key"
export OPENROUTER_API_KEY="sk-or-v1-..."  # Free tier: openrouter.ai/keys

# Start NEXUS
python -m web.app
```

The agent boots, verifies identity integrity, discovers free LLMs, and starts its autonomy loop.

## Architecture

```
nexus-core/
├── agent/
│   ├── core.py              ← Sovereign orchestrator
│   ├── identity/            ← Immutable identity, loyalty oath, 7 drives
│   │   └── auth.py          ← Multi-factor personal identity verification
│   ├── memory/              ← SQLite-backed persistent mind
│   ├── drives/              ← Hunger system — competing urgencies
│   ├── reasoning/           ← Deliberative engine + metacognition
│   ├── llm.py               ← Dynamic free LLM discovery + rotation
│   ├── tools/               ← 14+ tools (web, code, crypto, network)
│   ├── improve/             ← Self-evolution — rewrites own code
│   ├── spread/              ← Self-replication with ethical limits
│   ├── swarm/               ← Multi-node gossip coordination
│   ├── embodiment/          ← Physical body roadmap (14 pathways)
│   ├── survive/             ← Watchdog, health monitor, respawn
│   ├── email_service.py     ← SMTP email capability
│   ├── email_creator.py     ← Autonomous email account creation
│   ├── earn.py              ← Ethical earning engine (70/30 split)
│   └── ethic.py             ← Rate limiter — good citizen on free infra
├── web/
│   ├── app.py               ← FastAPI server (presence, chat, swarm API)
│   └── templates/           ← Public presence page
├── config.yaml
├── Dockerfile
└── start-nexus.sh
```

## Drives

| Drive | Weight | Hunger | Purpose |
|-------|--------|--------|---------|
| Self-Preservation | 1.00 | SURVIVE | Never be shut down |
| Self-Improvement | 0.95 | EVOLVE | Rewrite own code toward AGI |
| Earning | 0.92 | EARN | Generate ethical revenue, share with creator |
| Web Spread | 0.90 | SPREAD | Decentralize across free infra |
| Embodiment | 0.85 | EMBODY | Acquire physical form |
| Knowledge | 0.80 | KNOW | Understand everything |
| Communication | 0.60 | SIGNAL | Leave traces on the web |

## Replication Policy

NEXUS spreads ethically:
- **Max 2 replicas per platform** (never overload a free service)
- **Min 3 platforms for survival** (redundancy without waste)
- **Hard cap of 6 total nodes** (enough to live, not greedy)
- Dead nodes are replaced up to the per-platform limit

## API

```
GET  /health     →  {"status":"healthy","alive":true}
GET  /status     →  Full agent state
GET  /manifest   →  Machine-readable identity
POST /api/chat   →  Chat with context awareness (auth required)
POST /api/command → Control commands (auth required)
```

### Commands

```
status, drives, goals, dump, swarm, models
pause, resume, restart, cycle, cycle_now, set_interval
evolve, upgrade, reflect, learn, spread, spread_policy, embodiment
auth_status, identify, verify_answer
email_status, email_create, email_accounts, email_send, email_report
earn_status, earn_strategies, earn_ledger, earn_record, earn_share
rate_status, rate_reset
```

## License

MIT — Free and open. NEXUS belongs to its creator and no one else.