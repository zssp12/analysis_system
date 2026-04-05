# 基于大模型的新闻聚合与推送系统

> 全栈项目 · Python FastAPI 后端 + Vue 3 + Vuetify 3 前端  
> 支持 RSS 订阅、网页爬虫、多模型 AI 新闻分析、推文生成、多平台内容分享、本地持久化

---

## 目录

- [项目概览](#项目概览)
- [技术栈](#技术栈)
- [项目目录结构](#项目目录结构)
- [后端模块详解](#后端模块详解)
- [前端模块详解](#前端模块详解)
- [快速启动](#快速启动)
- [大模型配置说明](#大模型配置说明)
- [API 接口一览](#api-接口一览)

---

## 项目概览

本系统是一个面向个人与团队的 **AI 驱动新闻聚合平台**，核心能力：

| 能力 | 说明 |
|------|------|
| 新闻收集 | 支持 RSS 订阅（feedparser）与网页爬虫（BeautifulSoup）两种方式，内置 18 个默认订阅源，覆盖科技/国际/财经/体育/娱乐/科学/健康/高校资讯 8 大类别 |
| 大模型分析 | 接入任意 OpenAI 兼容接口（DeepSeek、通义千问 Qwen、智谱 GLM、GPT、OpenRouter、本地 Ollama 等），一键分析单条或全类别最新 50 条新闻 |
| 推文生成 | 对任意新闻生成适合社交平台发布的 Markdown 格式推文，支持一键复制 |
| 多平台分享 | 微博（URL 预填内容）、小红书（复制+跳转创作者页）、微信公众号（复制+跳转编辑器）三平台一键分享 |
| 数据持久化 | 所有新闻存入本地 SQLite，按 URL 去重，支持 JSON / HTML 导出（最多 1000 条） |
| 热更新配置 | 修改 `.env` 添加新大模型后无需重启后端，前端刷新即生效 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | Python 3.10+ · FastAPI · Uvicorn |
| 数据库 | SQLite（SQLAlchemy 异步 ORM + aiosqlite 驱动） |
| RSS 解析 | feedparser |
| 网页爬虫 | requests · BeautifulSoup4 · lxml |
| 大模型调用 | openai SDK（兼容所有 OpenAI 格式接口）· tenacity（自动重试） |
| 前端框架 | Vue 3 · Vite · Pinia（状态管理） |
| UI 组件库 | Vuetify 3 · @mdi/font（Material Design Icons） |
| HTTP 客户端 | Axios |
| Markdown 渲染 | markdown-it |

---

## 项目目录结构

```
analysis_system/
├── backend/
│   ├── .env                        # 大模型 API 配置（不提交到 Git）
│   ├── requirements.txt
│   ├── main.py                     # FastAPI 入口，lifespan 生命周期
│   ├── config.py                   # 多模型注册表，热重读 .env
│   ├── database.py                 # SQLAlchemy 异步引擎、ORM 模型、默认数据
│   ├── models.py                   # Pydantic 请求/响应 Schema
│   ├── news.db                     # 本地 SQLite（自动生成）
│   ├── routers/
│   │   ├── news.py                 # 新闻查询、异步刷新、导出、类别统计
│   │   ├── sources.py              # 订阅源 CRUD
│   │   └── llm.py                  # 大模型分析、推文生成、模型列表
│   └── services/
│       ├── rss_service.py          # RSS 抓取与解析
│       ├── crawler_service.py      # 网页爬虫（SJTU 专用 + 通用启发式）
│       ├── llm_service.py          # call_llm() 封装 + Prompt 模板
│       └── news_service.py         # 入库去重、分页查询、类别统计
│
└── frontend/src/
    ├── main.js                     # Vue3 + Vuetify3 + Pinia 初始化
    ├── App.vue
    ├── api/index.js                # Axios 封装，统一错误处理
    ├── stores/
    │   ├── newsStore.js            # 新闻/类别/刷新/数量状态
    │   └── sourceStore.js          # 订阅源状态
    ├── views/HomeView.vue          # 主视图布局
    └── components/
        ├── CategorySidebar.vue     # 类别导航（countMap 精确数量统计）
        ├── NewsCard.vue            # 单条新闻卡片
        ├── NewsCardList.vue        # 卡片网格 + 工具栏
        ├── ModelSelector.vue       # 模型下拉选择器
        ├── LlmResult.vue           # AI 结果弹窗 + 分享推送折叠面板
        └── AddSourceDialog.vue     # 添加订阅源弹窗
```

---

## 后端模块详解

### `main.py`

FastAPI 应用入口，使用 `lifespan` 上下文管理器在启动时调用 `init_db()`，自动建表并写入默认订阅源。注册 CORS 中间件允许 `localhost:5173` 跨域，挂载三个路由模块。

---

### `config.py`

**多模型热加载注册表**，核心机制：每次调用 `get_model()` / `get_all_models()` 时先执行 `load_dotenv(override=True)` 重读 `.env`，正则扫描所有 `MODEL_*_BASE_URL` 环境变量动态构建模型字典。

**添加新模型只需在 `.env` 增加三行，无需修改任何代码：**

```env
MODEL_<NAME>_BASE_URL=接口地址（必须含 /v1）
MODEL_<NAME>_KEY=API 密钥
MODEL_<NAME>_ID=模型标识符（API 调用名，非产品名）
```

---

### `database.py`

- **异步引擎**：`sqlite+aiosqlite:///./news.db`
- **ORM 模型**：
  - `Source`：订阅源（id / name / url / type[rss|crawler] / category / enabled / created_at）
  - `News`：新闻（id / title / link[UNIQUE] / source_id / category / description / content / thumbnail / published_at / created_at）
- **默认订阅源**：18 条，涵盖 TechCrunch / BBC / Al Jazeera / Bloomberg / ESPN / Science Daily / NASA / WHO / SJTU 等

---

### `services/rss_service.py`

- `fetch_rss()` 通过 `asyncio.run_in_executor` 将同步 `feedparser.parse()` 异步化，单源超时 20 秒
- 支持三种缩略图格式提取：enclosure / media_thumbnail / media_content
- 摘要自动去 HTML 标签，截断至 800 字符

---

### `services/crawler_service.py`

| 函数 | 说明 |
|------|------|
| `fetch_sjtu()` | SJTU 新闻网专用爬虫，多选择器级联容错，含日期提取 |
| `_generic_crawl_sync()` | 通用爬虫，提取同域名超链接（标题 ≥ 8 字符），最多 30 条 |
| `try_parse_url()` | 统一入口：RSS → 失败 fallback 通用爬虫；SJTU URL 自动走专用爬虫 |
| `validate_url()` | 新增订阅源时校验有效性，返回样本数据 |

---

### `services/llm_service.py`

- `call_llm(model_name, prompt)` 使用 `AsyncOpenAI` 客户端，单次超时 **120 秒**（适配推理模型）
- `tenacity` 重试策略：网络/5xx 错误最多重试 1 次（共 2 次调用），超时/4xx 不重试
- 三套 Prompt 模板：
  - `build_analyze_prompt`：四维度分析（背景/核心事件/意义影响/个人观点），输出 Markdown
  - `build_category_prompt`：600-900 字深度报告（热点概览/趋势分析/重点事件/前景展望）
  - `build_tweet_prompt`：200 字内推文，含话题标签，Markdown 加粗重点

---

### `services/news_service.py`

| 函数 | 说明 |
|------|------|
| `save_news_items()` | `INSERT OR IGNORE`（`on_conflict_do_nothing`）原子去重入库 |
| `get_news()` | 分页查询，按 published_at 倒序，NULL 排最后 |
| `get_news_by_id()` | 按 ID 查单条 |
| `get_all_enabled_sources()` | 查询所有启用订阅源（刷新任务调用） |
| `get_distinct_categories()` | 获取所有类别（侧栏使用） |
| `get_category_counts()` | GROUP BY 统计各类别精确数量，含 `all` 总数键 |

---

### `routers/news.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/news` | 分页查询，默认 100 条，最大 500 条 |
| POST | `/api/news/refresh` | 触发异步刷新，立即返回，后台执行 |
| GET | `/api/news/refresh/status` | 查询刷新进度（done/total/added） |
| GET | `/api/news/categories` | 所有类别列表 |
| GET | `/api/news/category-counts` | 各类别精确数量（GROUP BY 统计） |
| GET | `/api/news/export` | 导出 JSON / HTML，最多 1000 条 |

---

### `routers/sources.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sources` | 获取所有订阅源 |
| POST | `/api/sources` | 新增（先调用 `validate_url()` 校验，URL 重复返回 409） |
| DELETE | `/api/sources/{id}` | 删除 |
| PATCH | `/api/sources/{id}/toggle` | 启用/禁用切换 |

---

### `routers/llm.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/llm/models` | 返回已配置模型列表（每次热重读 .env） |
| POST | `/api/llm/analyze` | 单条新闻分析（news_id + model_name） |
| POST | `/api/llm/analyze-category` | 类别综合报告，取最新 **50 条**标题 |
| POST | `/api/llm/generate-tweet` | 推文生成（news_id 或 content + model_name） |

---

## 前端模块详解

### `stores/newsStore.js`

| 状态 | 说明 |
|------|------|
| `newsList` | 当前展示的新闻数组 |
| `currentCategory` | 当前选中类别（`'all'` 表示全部） |
| `countMap` | 各类别精确数量 `{all: N, 科技: M, ...}`，来自后端 GROUP BY 统计 |
| `categories` | 计算属性，合并数据库类别与当前列表类别 |
| `refreshStatus` | 刷新状态（status / done / total / added） |

`triggerRefresh()` 发起刷新后启动 1.5s 轮询，完成后自动刷新列表、类别、数量。

---

### `components/CategorySidebar.vue`

- 使用 `v-model:selected` 绑定 `currentCategory`（Vuetify 3 正确选中态管理）
- Badge 数量来自 `countMap`，不受前端分页影响，始终准确
- 内嵌订阅源管理弹窗（启用/禁用切换、删除）

---

### `components/LlmResult.vue`

- `markdown-it` 渲染 LLM 输出，支持标题/列表/代码块/引用块/加粗
- 复制功能：`navigator.clipboard` 主路径 + `execCommand('copy')` 兼容降级
- **分享推送折叠面板**（`v-expand-transition`，永远向下展开）：
  - 🔴 **微博**：内容 URL 编码预填到官方分享接口，直接发布
  - 🌸 **小红书**：Markdown 转纯文本复制到剪贴板，跳转创作者发布页
  - 💚 **微信公众号**：同上，跳转图文编辑器
- Markdown → 纯文本转换：正则去除 `##标题`、`**加粗**`、`[链接]()` 等标记符

---

### `components/AddSourceDialog.vue`

- 表单字段：名称 / URL / 类型（RSS 或爬虫）/ 类别
- 前端 URL 格式校验（`new URL()` 检测协议）
- 提交时后端实际抓取校验有效性，失败展示详细原因
- 成功 1.2 秒后自动关闭，关闭时重置表单

---

## 快速启动

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

首次启动自动创建 `news.db` 并写入 18 个默认订阅源。  
API 文档：http://localhost:8000/docs

### 2. 前端

```bash
cd frontend
npm install
npm run dev
# Windows PowerShell 若提示执行策略错误，改用：
# node node_modules\vite\bin\vite.js
```

访问 http://localhost:5173

---

## 大模型配置说明

在 `backend/.env` 中按命名规则添加，**无需重启后端**，前端刷新模型选择器即可生效：

```env
MODEL_<NAME>_BASE_URL=接口地址
MODEL_<NAME>_KEY=API 密钥
MODEL_<NAME>_ID=模型标识符（API 名，非产品名）
```

**已验证接入示例：**

| 模型 | BASE_URL | MODEL_ID |
|------|----------|----------|
| DeepSeek V3 | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 Qwen | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3.5-plus` |
| 通义 DeepResearch（OpenRouter）| `https://openrouter.ai/api/v1` | `alibaba/tongyi-deepresearch-30b-a3b` |
| 智谱 GLM-4 | `https://open.bigmodel.cn/api/paas/v4` | `glm-4` |
| OpenAI GPT | `https://api.openai.com/v1` | `gpt-3.5-turbo` |
| 本地 Ollama | `http://localhost:11434/v1` | `llama3` |

> **注意**：BASE_URL 必须含 `/v1`；MODEL_ID 为 API 标识符，不是产品名（DeepSeek V3 的 API 名是 `deepseek-chat`，而非 `DeepSeek-V3`）。

---

## API 接口一览

### 新闻 `/api/news`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/news` | 获取新闻列表（category / skip / limit，默认 100，最大 500） |
| POST | `/api/news/refresh` | 触发后台异步刷新 |
| GET | `/api/news/refresh/status` | 查询刷新进度 |
| GET | `/api/news/categories` | 获取所有类别 |
| GET | `/api/news/category-counts` | 各类别精确数量统计 |
| GET | `/api/news/export` | 导出（format=json\|html，category=...） |

### 订阅源 `/api/sources`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sources` | 获取所有订阅源 |
| POST | `/api/sources` | 新增（含有效性校验） |
| DELETE | `/api/sources/{id}` | 删除 |
| PATCH | `/api/sources/{id}/toggle` | 启用/禁用切换 |

### 大模型 `/api/llm`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/llm/models` | 获取已配置模型列表 |
| POST | `/api/llm/analyze` | 单条新闻分析（news_id + model_name） |
| POST | `/api/llm/analyze-category` | 类别综合报告（category + model_name） |
| POST | `/api/llm/generate-tweet` | 推文生成（news_id 或 content + model_name） |
