[![Русский](https://img.shields.io/badge/%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-181717?style=for-the-badge)](README.ru.md)

# WAnalyser

A Telegram bot for searching Warframe Market items and tracking prices. It shows offers from sellers who are in game and helps you follow selected items.

## Features

- Search by Russian item name, including inline search from other chats.
- Personal subscriptions to price changes.
- Profiles, premium access, and a referral balance.
- Administrator commands with role checks.

## Installation and startup

Requires Python 3.12–3.14, [uv](https://docs.astral.sh/uv/), PostgreSQL, Redis, and a public HTTPS proxy. Exact runtime and dependency versions are listed in [.python-version](.python-version) and [uv.lock](uv.lock).

```bash
uv sync --frozen
uv run --frozen python scripts/init_env.py
```

Fill in the generated `.env` using [.env.example](.env.example). Keep its permissions at `0600`. All settings are required:

| Setting            | Purpose                                                |
| ------------------ | ------------------------------------------------------ |
| `BOT_TOKEN`        | Bot token from BotFather                               |
| `BOT_NAME`         | This bot's username without `@`                        |
| `PG_DSN`           | Connection string for a dedicated PostgreSQL database   |
| `REDIS_URL`        | Redis address for rate limiting                        |
| `BASE_WEBHOOK_URL` | Public HTTPS origin without a trailing `/`              |
| `WEBHOOK_SECRET`   | Internal secret generated once by `init_env.py`         |

Use your own credentials. For remote PostgreSQL, enable TLS certificate verification through the DSN parameters. Create a dedicated database and role, then prepare the tables and start the bot:

```bash
uv run --frozen --env-file .env python setup.py
uv run --frozen --env-file .env python main.py
```

The server listens on `127.0.0.1:8080`. The HTTPS proxy must forward `/webhook` to this address without removing the `X-Telegram-Bot-Api-Secret-Token` header.

## Usage

Start with `/start`. Enable inline mode in BotFather to search from other chats. The database owner assigns administrators through the `users.admin` field; the role is checked again for administrative actions.

PostgreSQL stores Telegram IDs, names, subscriptions, and premium history; Redis stores request counters. `dictionary.json` contains the game item catalog. Messages and notifications go through Telegram, and prices are requested from Warframe Market. `.env`, database dumps, and user lists are kept out of Git.

## Checks

```bash
uv run --frozen python scripts/check.py
```

The command checks syntax, critical Ruff errors, isolated regression tests with `pytest -W error`, and dependency vulnerabilities. It does not send messages or connect to the production database.

## Limitations

Rankings are disabled in the interface. Premium access is arranged manually through Boosty; there is no automatic payment gateway. Drafts and the record of sent notifications are lost on restart.

External API compatibility and the full Telegram/PostgreSQL/Redis workflow require separate verification. See [STATUS.md](STATUS.md) (in Russian) for readiness details and remaining limitations.
