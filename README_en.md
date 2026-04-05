# LLM-Powered News Aggregation & Publishing System

> Full-stack project · Python FastAPI backend + Vue 3 + Vuetify 3 frontend  
> Supports RSS feeds, web crawling, multi-model AI news analysis, tweet generation, multi-platform content sharing, and local persistence

**[中文文档 README.md](./README.md)**

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Backend Modules](#backend-modules)
- [Frontend Modules](#frontend-modules)
- [Quick Start](#quick-start)
- [LLM Configuration](#llm-configuration)
- [API Reference](#api-reference)

---

## Project Overview

An **AI-driven news aggregation platform** for individuals and teams, with the following core capabilities:

| Feature | Description |
|---------|-------------|
| News Collection | Supports RSS feeds (feedparser) and web crawlers (BeautifulSoup), with 18 built-in default sources covering 8 categories: Tech / International / Finance / Sports / Entertainment / Science / Health / University News |
| AI Analysis | Compatible with any OpenAI-format API (DeepSeek, Qwen, GLM, GPT, OpenRouter, local Ollama, etc.), one-click analysis of single articles or the latest 50 articles in any category |
| Tweet Generation | Generates Markdown-formatted social media posts for any article, with one-click copy |
| Multi-Platform Sharing | Share to Weibo (URL pre-fill), Xiaohongshu (copy + redirect), WeChat Official Account (copy + redirect to editor) |
| Data Persistence | All news stored in local SQLite, deduplicated by URL, exportable as JSON / HTML (up to 1,000 records) |
| Hot-Reload Config | Add new LLM models in `.env` without restarting the backend — effective immediately on frontend refresh |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend Framework | Python 3.10+ · FastAPI · Uvicorn |
| Database | SQLite (SQLAlchemy async ORM + aiosqlite driver) |
| RSS Parsing | feedparser |
| Web Crawling | requests · BeautifulSoup4 · lxml |
| LLM Calling | openai SDK (compatible with all OpenAI-format APIs) · tenacity (auto-retry) |
| Frontend Framework | Vue 3 · Vite · Pinia (state management) |
| UI Component Library | Vuetify 3 · @mdi/font (Material Design Icons) |
| HTTP Client | Axios |
| Markdown Rendering | markdown-it |

---

## Project Structure

```
analysis_system/
├── backend/
│   ├── .env                        # LLM API config (do not commit to Git)
│   ├── requirements.txt
│   ├── main.py                     # FastAPI entry point, lifespan hooks
│   ├── config.py                   # Multi-model registry, hot-reload .env
│   ├── database.py                 # SQLAlchemy async engine, ORM models, seed data
│   ├── models.py                   # Pydantic request/response schemas
│   ├── news.db                     # Local SQLite file (auto-generated)
│   ├── routers/
│   │   ├── news.py                 # News query, async refresh, export, category stats
│   │   ├── sources.py              # Source CRUD
│   │   └── llm.py                  # LLM analysis, tweet generation, model list
│   └── services/
│       ├── rss_service.py          # RSS fetch & parse
│       ├── crawler_service.py      # Web crawler (SJTU-specific + generic heuristic)
│       ├── llm_service.py          # call_llm() wrapper + Prompt templates
│       └── news_service.py         # DB insert (dedup), paginated query, category stats
│
└── frontend/src/
    ├── main.js                     # Vue3 + Vuetify3 + Pinia setup
    ├── App.vue
    ├── api/index.js                # Axios wrapper, unified error handling
    ├── stores/
    │   ├── newsStore.js            # News / category / refresh / counts state
    │   └── sourceStore.js          # Sources state
    ├── views/HomeView.vue          # Main layout
    └── components/
        ├── CategorySidebar.vue     # Category nav (accurate countMap badges)
        ├── NewsCard.vue            # Single news card
        ├── NewsCardList.vue        # Card grid + toolbar
        ├── ModelSelector.vue       # Model dropdown selector
        ├── LlmResult.vue           # AI result dialog + share panel
        └── AddSourceDialog.vue     # Add source dialog with URL validation
```

---

## Backend Modules

### `main.py`

FastAPI entry point. Uses the `lifespan` context manager to call `init_db()` on startup (creates tables and seeds default sources). Registers CORS middleware to allow `localhost:5173` cross-origin requests. Mounts three router modules.

---

### `config.py`

**Multi-model hot-reload registry.** On every call to `get_model()` / `get_all_models()`, it runs `load_dotenv(override=True)` to re-read `.env`, then scans all `MODEL_*_BASE_URL` environment variables via regex to dynamically build the model dictionary.

**To add a new model, just add three lines to `.env` — no code changes needed:**

```env
MODEL_<NAME>_BASE_URL=https://api.example.com/v1
MODEL_<NAME>_KEY=your-api-key
MODEL_<NAME>_ID=model-identifier   # API name, not product name
```

---

### `database.py`

- **Async engine**: `sqlite+aiosqlite:///./news.db`
- **ORM models**:
  - `Source`: id / name / url / type[rss|crawler] / category / enabled / created_at
  - `News`: id / title / link[UNIQUE] / source_id / category / description / content / thumbnail / published_at / created_at
- **Default sources**: 18 pre-seeded entries covering TechCrunch, BBC, Al Jazeera, Bloomberg, ESPN, Science Daily, NASA, WHO, SJTU, etc.

---

### `services/rss_service.py`

- `fetch_rss()` wraps synchronous `feedparser.parse()` with `asyncio.run_in_executor` to avoid blocking the event loop; 20-second per-source timeout
- Extracts thumbnails from three formats: enclosure / media_thumbnail / media_content
- Summaries are HTML-stripped and truncated to 800 characters

---

### `services/crawler_service.py`

| Function | Description |
|----------|-------------|
| `fetch_sjtu()` | Dedicated SJTU news crawler with multi-selector fallback and date extraction |
| `_generic_crawl_sync()` | Generic heuristic crawler: extracts same-domain `<a>` links (title ≥ 8 chars), up to 30 items |
| `try_parse_url()` | Unified entry: tries RSS first, falls back to crawler on empty; SJTU URLs automatically use the dedicated crawler |
| `validate_url()` | URL validation on source creation; returns sample data |

---

### `services/llm_service.py`

- `call_llm(model_name, prompt)` uses `AsyncOpenAI` client, **120-second timeout** per request (accommodates reasoning models)
- Retry policy via `tenacity`: retries once (2 calls total) for network errors and HTTP 5xx; no retry for timeouts or 4xx
- Three Prompt templates:
  - `build_analyze_prompt`: 4-dimension analysis (background / key events / significance / perspective), Markdown output
  - `build_category_prompt`: 600–900 word deep report (highlights / trend analysis / notable events / outlook)
  - `build_tweet_prompt`: ≤200-character post with hashtags and bolded keywords

---

### `services/news_service.py`

| Function | Description |
|----------|-------------|
| `save_news_items()` | Atomic dedup insert via `INSERT OR IGNORE` (`on_conflict_do_nothing` on `link`) |
| `get_news()` | Paginated query, sorted by `published_at` DESC (NULLs last) |
| `get_news_by_id()` | Single article by ID |
| `get_all_enabled_sources()` | All enabled sources (used by refresh task) |
| `get_distinct_categories()` | All category values in DB (used by sidebar) |
| `get_category_counts()` | GROUP BY count per category, includes `all` total key |

---

### `routers/news.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/news` | Paginated list (default 100, max 500) |
| POST | `/api/news/refresh` | Trigger async refresh; returns immediately, runs in background |
| GET | `/api/news/refresh/status` | Refresh progress (done/total/added) |
| GET | `/api/news/categories` | All category names |
| GET | `/api/news/category-counts` | Exact count per category (GROUP BY) |
| GET | `/api/news/export` | Export JSON / HTML, up to 1,000 records |

---

### `routers/sources.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sources` | List all sources |
| POST | `/api/sources` | Create with `validate_url()` check; returns 409 on duplicate URL |
| DELETE | `/api/sources/{id}` | Delete |
| PATCH | `/api/sources/{id}/toggle` | Toggle enabled/disabled |

---

### `routers/llm.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/llm/models` | List configured models (hot-reloads `.env` on every call) |
| POST | `/api/llm/analyze` | Single-article analysis (news_id + model_name) |
| POST | `/api/llm/analyze-category` | Category summary report using latest **50** titles |
| POST | `/api/llm/generate-tweet` | Tweet generation (news_id or content + model_name) |

---

## Frontend Modules

### `stores/newsStore.js`

| State | Description |
|-------|-------------|
| `newsList` | Currently displayed news array |
| `currentCategory` | Selected category (`'all'` = everything) |
| `countMap` | Exact counts per category `{all: N, Tech: M, ...}` from backend GROUP BY |
| `categories` | Computed: merged DB + current list categories, deduped and sorted |
| `refreshStatus` | `{status, done, total, added}` |

`triggerRefresh()` starts a 1.5s polling loop; on completion, it automatically updates the list, categories, and counts.

---

### `components/CategorySidebar.vue`

- Uses `v-model:selected` binding on `currentCategory` (correct Vuetify 3 selection state management)
- Badge counts from `countMap` — always accurate, unaffected by frontend pagination
- Embedded source management dialog (toggle / delete)

---

### `components/LlmResult.vue`

- `markdown-it` renders LLM output with full styling (headings, lists, code blocks, blockquotes, bold)
- Copy: `navigator.clipboard` primary path + `execCommand('copy')` fallback
- **Share panel** (`v-expand-transition`, always expands downward):
  - 🔴 **Weibo**: URL-encodes content into official share endpoint, opens pre-filled
  - 🌸 **Xiaohongshu**: Strips Markdown to plain text, copies to clipboard, opens creator publish page
  - 💚 **WeChat Official Account**: Same, opens article editor
- Markdown → plain text: regex strips `## headers`, `**bold**`, `` `code` ``, `[links]()`, etc.

---

### `components/AddSourceDialog.vue`

- Fields: name / URL / type (RSS or crawler toggle) / category
- Frontend URL format validation (`new URL()` protocol check)
- On submit, backend actually fetches the URL to validate — displays detailed error on failure
- Auto-closes 1.2s after success; resets form on close

---

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

On first run, `news.db` is created and 18 default sources are seeded.  
Interactive API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# On Windows PowerShell with execution policy restrictions, use:
# node node_modules\vite\bin\vite.js
```

Open http://localhost:5173

---

## LLM Configuration

Add entries to `backend/.env` — **no backend restart needed**, just refresh the frontend:

```env
MODEL_<NAME>_BASE_URL=https://api.provider.com/v1
MODEL_<NAME>_KEY=your-api-key
MODEL_<NAME>_ID=model-identifier
```

**Verified configurations:**

| Model | BASE_URL | MODEL_ID |
|-------|----------|----------|
| DeepSeek V3 | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Alibaba Qwen | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3.5-plus` |
| Tongyi DeepResearch (OpenRouter) | `https://openrouter.ai/api/v1` | `alibaba/tongyi-deepresearch-30b-a3b` |
| Zhipu GLM-4 | `https://open.bigmodel.cn/api/paas/v4` | `glm-4` |
| OpenAI GPT | `https://api.openai.com/v1` | `gpt-3.5-turbo` |
| Local Ollama | `http://localhost:11434/v1` | `llama3` |

> **Important**: `BASE_URL` must include `/v1`. `MODEL_ID` is the API identifier, not the product name (e.g., DeepSeek V3's API name is `deepseek-chat`, not `DeepSeek-V3`).

---

## API Reference

### News `/api/news`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/news` | List news (category / skip / limit, default 100, max 500) |
| POST | `/api/news/refresh` | Trigger async background refresh |
| GET | `/api/news/refresh/status` | Refresh progress |
| GET | `/api/news/categories` | All category names |
| GET | `/api/news/category-counts` | Per-category count statistics |
| GET | `/api/news/export` | Export (format=json\|html, category=...) |

### Sources `/api/sources`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sources` | List all sources |
| POST | `/api/sources` | Create with validation |
| DELETE | `/api/sources/{id}` | Delete |
| PATCH | `/api/sources/{id}/toggle` | Toggle enabled state |

### LLM `/api/llm`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/llm/models` | List configured models |
| POST | `/api/llm/analyze` | Single article analysis (news_id + model_name) |
| POST | `/api/llm/analyze-category` | Category summary (category + model_name) |
| POST | `/api/llm/generate-tweet` | Tweet generation (news_id or content + model_name) |
