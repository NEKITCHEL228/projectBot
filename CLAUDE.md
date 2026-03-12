# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot implementing a **stock exchange game** ("Биржа"): players start with equal funds and buy/sell company shares across trading rounds. The bot supports multiple simultaneous chats, and all game state persists in PostgreSQL.

Stack:
- **Python backend** (`app/backend/`) — aiohttp web server + Telegram bot logic
- **React frontend** (`app/frontend/`) — admin/game UI (early stage, mostly template)
- **PostgreSQL** via Docker Compose; all DB access via **SQLAlchemy async** (`asyncpg` driver)
- **Alembic** for migrations
- **aiohttp-apispec** — Swagger docs auto-generated at `/docs` (JSON at `/docs/json`)

## Commands

### Database

```bash
docker compose up -d      # Start PostgreSQL on localhost:5432
docker compose down       # Stop
```

### Backend

```bash
source .venv/Scripts/activate   # Windows bash

python main.py            # Run the bot (aiohttp on default port 8080)

alembic upgrade head      # Apply migrations
alembic revision --autogenerate -m "description"  # Generate migration (set target_metadata first)
```

### Frontend (`app/frontend/`)

```bash
yarn              # Install dependencies
yarn dev          # Dev server at http://localhost:5173
yarn build        # tsc + vite build
yarn lint         # ESLint
```

## Architecture

### App startup flow

`main.py` → `setup_app(config_path)` in `app/backend/web/app.py`:
1. Logging, config (`config.yml`), encrypted cookie session
2. Routes, aiohttp-apispec, middlewares
3. `setup_store(app)` — instantiates all accessors

### BaseAccessor pattern

All service/data classes inherit `BaseAccessor` (`app/backend/base/base_accessor.py`). The constructor registers `connect` / `disconnect` on `app.on_startup` / `app.on_cleanup`, so lifecycle is managed automatically by aiohttp. Every new accessor (DB, TG API, bot manager, etc.) must follow this pattern.

### Backend layers

```
app/backend/
  web/          — aiohttp app factory, config loader, middlewares, routes, utils
  store/
    database/   — SQLAlchemy engine/session setup, DeclarativeBase
    tg_api/     — Telegram Bot API HTTP client (aiohttp ClientSession, reused across requests)
    bot/        — bot update routing/handling
    game/       — game session accessor (DB operations for game state)
    admin/      — admin accessor (DB operations for admin)
  admin/        — HTTP views, routes, marshmallow schemes for admin API
  game/         — HTTP views, routes, marshmallow schemes for game API
  base/         — BaseAccessor
```

### Database schema

Six tables (defined in `Project.txt`):
- `player` — TG user record, lifetime stats (max_balance, games_count, games_win)
- `game` — game session per chat (status, current round, max_rounds)
- `game_player` — M2M between game and player
- `player_balance` — per-game balance (full, cash, share value)
- `company_shares` — available shares per game with current price
- `player_company_share` — shares held by a player in a game

### Alembic

`alembic/env.py` has `target_metadata = None` — **must be replaced** with the SQLAlchemy `Base.metadata` from `store/database/sqlalchemy_base.py` before `--autogenerate` will detect model changes.

### aiohttp ClientSession

Created once in `store/tg_api/` on startup; reused for all Telegram API calls. Never instantiate a new `ClientSession` per request.

### Frontend (`app/frontend/src/`)

- State: **MobX** classes with `makeAutoObservable`, components wrapped with `observer()`
- Server state: **TanStack Query**
- UI: **Ant Design**
- Styles: **CSS Modules** (`import s from './Component.module.css'`)
- Routing: **React Router v7**

### Configuration

`config.yml` — bot token and DB credentials. DB credentials match `docker-compose.yml` exactly.

## Правила

Правила оформления коммитов: [.claude/rules/backend/commits.md](.claude/rules/backend/commits.md)

Правила написания кода (backend): [.claude/rules/backend/code_style.md](.claude/rules/backend/code_style.md)
