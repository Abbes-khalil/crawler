# AS Biz Dev — Web Intelligence

A local web application that crawls a company website, cleans the HTML into
readable text, and mechanically extracts factual contact information (emails,
phones, addresses, social links, JSON-LD) with full provenance.

**What it does:** given a company website, it discovers useful public pages,
crawls a limited, category-diverse selection of them, and returns structured
observations — each with `raw_value`, `normalized_value`, `source_url`,
`source_type`, and `confidence`.

**What it does not do:** classify companies, score commercial relevance,
infer industry, or produce recommendations. That interpretation layer is
owned by a separate orchestration agent.

## How it runs

The user launches one executable. It starts a local HTTP server on
`127.0.0.1`, waits for `/api/health`, then opens the default browser at
`http://127.0.0.1:8765`. The whole UI runs in the browser; crawling runs
locally. No cloud backend, no Docker, no separately installed runtime, no
terminal.

```
launcher/__main__.py
   |
   +-- already running? (lock file + /api/health) --> open browser, exit
   |
   +-- pick a free port from 8765 upward
   +-- start uvicorn on 127.0.0.1:<port> (background thread)
   +-- wait for GET /api/health
   +-- open the default browser
   +-- run until Ctrl-C / quit, then shut down and clear the lock
```

## Architecture

```
web/                     Next.js 16 frontend, output: "export" -> web/out/
                         Served as static files by the API in production;
                         API calls are same-origin (/api/*).
app/
├── main.py              FastAPI app: /api routers + static SPA serving
├── config.py            Env-driven settings, local-first defaults
├── paths.py             Cross-platform app-data locations (platformdirs)
├── api/
│   ├── health.py        GET /api/health, GET /api/status
│   ├── crawl.py         POST /api/crawl  -> job id (202)
│   ├── jobs.py          GET /api/jobs, GET /api/jobs/{id},
│   │                    POST /api/jobs/{id}/cancel
│   └── results.py       GET /api/results, GET /api/results/{id}
├── jobs/
│   └── manager.py       In-process asyncio job registry (no queue/broker)
├── crawler/             Unchanged crawl pipeline (httpx + optional Playwright)
├── extraction/          Unchanged: emails, phones, addresses, JSON-LD, social
├── models/              Pydantic request/response/observation models
└── storage/
    ├── db.py            SQLAlchemy engine + ORM (SQLite by default, WAL)
    ├── companies.py pages.py observations.py   upserts
    └── results.py       read-side queries for GET /api/results
launcher/__main__.py     Lifecycle: single-instance, port, server, browser
packaging/               PyInstaller spec + Windows/macOS installer scripts
```

## Local data

Everything user-generated lives under the per-user app-data directory,
never inside the installed bundle:

| OS | Path |
|---|---|
| Windows | `%LOCALAPPDATA%\AS Biz Dev Web Intelligence\` |
| macOS | `~/Library/Application Support/AS Biz Dev Web Intelligence/` |
| Linux | `~/.local/share/AS Biz Dev Web Intelligence/` |

Contents: `asbizdev.db` (SQLite), `logs/app.log`, `asbizdev.lock`.

## Development

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8765
```

Frontend (dev server, proxies to the backend via `NEXT_PUBLIC_CRAWLER_API`):

```powershell
npm --prefix web ci
npm --prefix web run dev        # http://localhost:3000
```

Run the whole app the way an end user would:

```powershell
npm --prefix web run build      # produces web/out/
python -m launcher              # serves web/out/ and opens the browser
```

Optional Playwright fallback for JS-rendered pages (disabled in packaged
builds):

```powershell
python -m playwright install chromium
```

## Environment variables

All optional — the app runs with local-first defaults. Copy `.env.example`
to `.env` to override.

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address. Do not set to `0.0.0.0`. |
| `PREFERRED_PORT` | `8765` | First port tried; the launcher scans upward if busy. |
| `DATABASE_URL` | SQLite in app-data dir | Any SQLAlchemy URL (e.g. Postgres) to override. |
| `DEFAULT_MAX_PAGES` | `5` | Default page cap per crawl. |
| `MAX_CRAWL_PAGES` | `20` | Hard upper bound on `max_pages`. |
| `CRAWLER_USER_AGENT` | `ASBizDevCrawler/0.1` | User-Agent sent on every request. |
| `REQUEST_TIMEOUT` | `15` | Per-request timeout (seconds). |
| `RESPECT_ROBOTS_TXT` | `true` | Honor robots.txt disallow rules. |
| `SITEMAP_MAX_URLS` | `200` | Cap on URLs from sitemap discovery. |
| `PLAYWRIGHT_ENABLED` | `true` (source) / `false` (packaged) | Allow the Playwright fallback. |
| `FRONTEND_ORIGIN` | `localhost:3000`, `127.0.0.1:3000` | CORS allow-list for the dev server only. |

## API

All routes are under `/api`. In production the frontend is same-origin, so
CORS is not needed.

### `GET /api/health`
`{ "status": "ok" }` — the launcher polls this before opening the browser.

### `GET /api/status`
App version, active/total job counts, `playwright_enabled`, `database_url`.

### `POST /api/crawl`
Request: `{ "website": "https://company.com", "max_pages": 5 }`

- `website` — required; scheme optional (`company.com` → `https://company.com`).
  Loopback / private / link-local hosts are rejected (422).
- `max_pages` — optional, 1–`MAX_CRAWL_PAGES`, default 5.

Returns `202` with a job object (`id`, `status`, `progress`, timestamps).

### `GET /api/jobs/{id}`
The job object, plus `result` (a full `CrawlCompanyResponse`) once complete.

`status`: `starting` → `crawling` → `completed` | `failed` | `cancelled`.
`progress`: `{ phase, pages_done, pages_total }`.

### `POST /api/jobs/{id}/cancel`
Requests cancellation of a running job (`202`); `409` if already terminal.

### `GET /api/results` / `GET /api/results/{company_id}`
List persisted crawls (canonical URL, page/observation counts, timestamp),
and full detail (pages + observations) for one.

## Status codes

| Status | Meaning |
|---|---|
| `SUCCESS` | All selected pages crawled successfully |
| `PARTIAL_SUCCESS` | At least one page crawled, at least one failed |
| `INVALID_URL` | Input could not be normalized into a usable URL |
| `DEAD_DOMAIN` | Homepage connection failed (DNS/refused) |
| `TIMEOUT` | Homepage request timed out |
| `BLOCKED` | Homepage returned HTTP 403 |
| `HTTP_ERROR` | Homepage returned another 4xx/5xx or a network error |
| `INSUFFICIENT_CONTENT` | Pages fetched but no readable text extracted |
| `ROBOTS_DENIED` | robots.txt disallows crawling under `RESPECT_ROBOTS_TXT` |
| `CAPTCHA` | Reserved (not detected yet) |

## Contact extraction

Extraction priority: `mailto:`/`tel:` links and JSON-LD Organization data
(confidence 0.95–1.0) → OpenGraph/social links (1.0 for links, 0.6 for the
`site_name` fallback) → regex fallback over visible text (0.7 emails, 0.4
phones, 0.4 addresses). Every fact is an `Observation` with provenance,
never a bare string. Confidence reflects *extraction reliability*, not
commercial relevance.

Phone numbers are validated with `phonenumbers` but never normalized by
guessing a country: `normalized_value` is populated only when the raw value
carries an explicit `+` country code, or for `tel:`/JSON-LD phones where a
deterministic ccTLD hint (`.fr` → `FR`) lets `phonenumbers` confirm a valid
number. Free-text regex matches are noise-filtered but never normalized.

## Packaging

```powershell
npm --prefix web ci ; npm --prefix web run build
python -m pip install -r requirements-build.txt
pyinstaller packaging/launcher.spec --noconfirm
```

- Windows: `dist\AS Biz Dev Web Intelligence.exe` (onefile); wrap with
  `packaging\windows\installer.iss` (Inno Setup, per-user, no admin).
- macOS: `dist/AS Biz Dev Web Intelligence.app`; `packaging/macos/build_app.sh`
  builds a `.dmg`. With `CODESIGN_IDENTITY` / `NOTARY_PROFILE` set it signs and
  notarizes; otherwise it ad-hoc signs the bundle (no paid Apple account).
- CI: `.github/workflows/build.yml` builds both on `workflow_dispatch` and
  on `v*` tags.

### Opening on macOS (unsigned build)

Without an Apple Developer ID ($99/yr) the build is not notarized, so
Gatekeeper shows *"can't be opened because Apple cannot check it for
malicious software."* The app is safe to run; use either workaround:

- **Right-click → Open** on the `.app`, then confirm once in the dialog.
  macOS remembers the choice for that copy.
- Or strip the quarantine flag from a terminal:

  ```bash
  xattr -dr com.apple.quarantine "/Applications/AS Biz Dev Web Intelligence.app"
  ```

## Tests

```powershell
pytest                      # backend
npm --prefix web run test   # frontend
```

The backend suite covers URL normalization, page scoring/selection, link
discovery, email/phone/address extraction, metadata/OpenGraph, JSON-LD,
social links, robots.txt, sitemap discovery, content hashing, observation
dedup, the SSRF host guard, and the full job-based `/api/crawl` → `/api/jobs`
flow against local fixtures and a temp SQLite DB. Network-facing modules are
tested with `httpx.MockTransport`; the suite never touches live websites.

## Integration contract

Call conceptually as `crawl_company(website, max_pages)`. This service
returns facts and evidence only — normalized text and structured contact
observations with provenance. It performs no classification, scoring, or
commercial interpretation.
