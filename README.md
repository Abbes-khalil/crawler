# AS Biz Dev — B2B Web Intelligence Crawler

A deterministic, generic web observation and extraction service.

**What it does:** given a company website, it discovers useful public pages,
crawls a limited, category-diverse selection of them, cleans the HTML into
readable text, and mechanically extracts factual information (emails,
phones, metadata) with full provenance.

**What it does not do:** classify companies, score commercial relevance,
infer industry, or produce recommendations. That interpretation layer is
owned by a separate ChatGPT orchestration agent. This service only answers:
*"What does this public website actually contain, and where did each fact
come from?"*

## Architecture

```
app/
├── main.py              FastAPI app, router registration
├── config.py             Env-driven settings
├── api/
│   ├── crawl.py           POST /crawl-company (+ best-effort persistence)
│   └── health.py          GET /health
├── crawler/
│   ├── orchestrator.py    Coordinates the whole crawl, builds the response
│   ├── url_normalizer.py  Scheme/host/trailing-slash/query normalization
│   ├── http_fetcher.py    Shared httpx.AsyncClient wrapper, basic retries
│   ├── link_discovery.py  Same-domain link extraction from HTML
│   ├── page_ranker.py     FR/EN keyword scoring + category-diverse selection
│   ├── robots.py          robots.txt fetch/parse, allow/deny + sitemap refs
│   ├── sitemap.py         /sitemap.xml + sitemap-index discovery (same-domain only)
│   └── browser_fetcher.py Lazy single-instance Playwright fallback
├── extraction/
│   ├── cleaner.py          Trafilatura text extraction + SHA-256 content hash
│   ├── metadata.py         title / meta description / OpenGraph / <html lang>
│   ├── emails.py            Regex email matcher (fallback source)
│   ├── phones.py            Regex phone matcher (fallback source, noise-filtered)
│   ├── contact_links.py     mailto:/tel: link extraction (primary source)
│   ├── jsonld.py             Organization/LocalBusiness JSON-LD parsing
│   ├── social_links.py       LinkedIn/Facebook/Instagram/YouTube/Twitter links
│   ├── addresses.py          Postal-code/city heuristic (low-confidence fallback)
│   └── observations.py      Builds structured, source-aware Observation objects
├── models/
│   ├── request.py    CrawlCompanyRequest
│   ├── response.py   CrawlCompanyResponse, CrawlMetrics, CrawlStatus
│   ├── page.py       CrawledPage, PageError
│   └── observation.py Observation
└── storage/
    ├── db.py             SQLAlchemy engine/session + ORM tables (Postgres/Supabase)
    ├── companies.py       get-or-create company row
    ├── pages.py           upsert crawled pages
    └── observations.py    insert observations (dedup via unique constraint)
```

Persistence is opt-in and best-effort: it only activates when `DATABASE_URL`
is set, and a database failure is logged but never fails the API response —
the crawl already succeeded from the caller's point of view.

## Installation (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Environment variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Environment label |
| `CRAWLER_USER_AGENT` | `ASBizDevCrawler/0.1` | User-Agent sent on every request |
| `DEFAULT_MAX_PAGES` | `5` | Default page cap when not specified |
| `REQUEST_TIMEOUT` | `15` | Per-request timeout, in seconds |
| `REQUEST_RETRY_COUNT` | `1` | Retries on timeout/connection failure per request |
| `RESPECT_ROBOTS_TXT` | `true` | Honor robots.txt disallow rules |
| `SITEMAP_MAX_URLS` | `200` | Cap on URLs pulled from sitemap discovery |
| `PLAYWRIGHT_ENABLED` | `true` | Allow the Playwright fallback for JS-shell pages |
| `PLAYWRIGHT_MIN_CONTENT_CHARS` | `200` | Below this many readable chars, HTML is "insufficient" |
| `PLAYWRIGHT_TIMEOUT_MS` | `15000` | Playwright page-load timeout |
| `DATABASE_URL` | *(unset)* | Postgres/Supabase connection string; persistence is disabled when empty |

Playwright also needs its browser binary installed once:

```powershell
python -m playwright install chromium
```

## Run

```powershell
python -m uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## API

### `GET /health`

```json
{ "status": "ok" }
```

### `POST /crawl-company`

Request:

```json
{ "website": "https://company.com", "max_pages": 5 }
```

- `website` — required. Scheme is optional (`company.com` is normalized to
  `https://company.com`).
- `max_pages` — optional, 1–20, default 5.

Response (abridged):

```json
{
  "status": "SUCCESS",
  "canonical_url": "https://company.com",
  "pages_discovered": 42,
  "pages_selected": 5,
  "pages_crawled": 5,
  "pages_failed": 0,
  "pages": [
    {
      "url": "https://company.com",
      "title": "...",
      "meta_description": "...",
      "language": "en",
      "text": "...",
      "status_code": 200,
      "crawl_method": "http",
      "content_hash": "..."
    }
  ],
  "page_errors": [],
  "observations": [
    {
      "field": "email",
      "raw_value": "Contact@Example.com",
      "normalized_value": "contact@example.com",
      "source_url": "https://company.com/contact",
      "source_type": "mailto_link",
      "observed_at": "2026-08-21T18:43:09.483881Z",
      "confidence": 1.0
    },
    {
      "field": "linkedin_url",
      "raw_value": "https://www.linkedin.com/company/example",
      "normalized_value": "https://www.linkedin.com/company/example",
      "source_url": "https://company.com",
      "source_type": "social_link",
      "observed_at": "2026-08-21T18:43:09.483881Z",
      "confidence": 1.0
    }
  ],
  "metrics": { "duration_ms": 4200, "http_pages": 5, "playwright_pages": 0 }
}
```

Observation `field` values now include: `email`, `phone`, `organization_name`,
`address`, `city`, `country`, `linkedin_url`, `facebook_url`, `instagram_url`,
`youtube_url`, `twitter_url`. `source_type` now includes `json_ld` and
`social_link` in addition to `mailto_link`/`tel_link`/`visible_text`/`metadata`.

## Status codes

| Status | Meaning |
|---|---|
| `SUCCESS` | All selected pages crawled successfully |
| `PARTIAL_SUCCESS` | At least one page crawled, at least one failed |
| `INVALID_URL` | Input could not be normalized into a usable URL |
| `DEAD_DOMAIN` | Homepage connection failed (DNS/refused) |
| `TIMEOUT` | Homepage request timed out |
| `BLOCKED` | Homepage returned HTTP 403 |
| `HTTP_ERROR` | Homepage returned another 4xx/5xx, or a non-timeout/connect network error |
| `INSUFFICIENT_CONTENT` | Pages fetched (HTTP and, if enabled, Playwright) but no readable text extracted from any |
| `ROBOTS_DENIED` | robots.txt disallows crawling the homepage under `RESPECT_ROBOTS_TXT` |
| `CAPTCHA` | Reserved for a future sprint (not detected yet) |

A technical crawl failure is never conflated with commercial irrelevance —
those are separate concerns owned by different layers of the system.

## Contact extraction

Extraction priority: `mailto:`/`tel:` links and JSON-LD Organization data
(confidence 0.95–1.0) → OpenGraph/social links (1.0 for links, 0.6 for the
`site_name` fallback) → regex fallback over visible text (0.7 emails, 0.4
phones, 0.4 addresses). Every fact is returned as an `Observation` with
`raw_value`, `normalized_value`, `source_url`, `source_type`, and
`confidence` — never as a bare string. Confidence reflects *extraction
reliability*, not commercial relevance.

Phone numbers are validated with `phonenumbers`, but **never** normalized by
guessing a country. `normalized_value` is only populated when the raw value
already carries an explicit `+` country code, or for `tel:`/JSON-LD phones
where a deterministic ccTLD hint (e.g. `.fr` → `FR`) lets `phonenumbers`
confirm a genuinely valid number — the hint is used only to *validate*, never
to fabricate a value when validation fails. Free-text regex matches are
additionally filtered for obvious non-phone noise (copyright year ranges,
implausible digit counts, long repeated-digit runs) but are never
normalized, regardless of any hint.

## Tests

```powershell
pytest
```

Unit tests cover URL normalization, page scoring/category selection, link
discovery, email/phone regex extraction (including the noise filter),
metadata/OpenGraph extraction, JSON-LD parsing, social link extraction,
address heuristics, robots.txt parsing, sitemap discovery, content hashing,
and observation deduplication. Network-facing modules (robots, sitemap) are
tested with `httpx.MockTransport`; the integration test drives the full
`/crawl-company` endpoint against local HTML fixtures (`tests/fixtures/`)
with `fetch_page`/`fetch_robots_policy`/`discover_sitemap_urls` monkeypatched
— the automated suite never depends on live websites. `pytest.ini` sets
`asyncio_mode = auto` for the async network tests.

## Sprint roadmap

- **Sprint 1:** FastAPI service, URL normalization, HTTP-only fetch, link
  discovery, category-diverse page ranking/selection, Trafilatura cleaning,
  structured contact observations, content hashing, status model, structured
  page errors, unit + integration tests.
- **Sprint 2 (this release):** Playwright fallback for JS-rendered pages,
  `robots.txt` + sitemap discovery, JSON-LD/OpenGraph extraction, social
  links, address heuristics, `phonenumbers`-based phone validation,
  PostgreSQL/Supabase persistence (opt-in via `DATABASE_URL`).
- **Sprint 3:** `POST /crawl-batch` + `GET /jobs/{job_id}`, Redis/RQ async
  job queue, per-domain rate limiting, retry/backoff, job history, metrics.

## Known limitations (Sprint 2)

- The address heuristic (`extraction/addresses.py`) is a loose postal-code +
  city regex — it is not a real address parser and is only used as a
  low-confidence fallback when no JSON-LD address is present.
- `phonenumbers`-based validation for `tel:`/JSON-LD phones uses a
  deterministic ccTLD → region hint (`.fr` → `FR`, etc.) to attempt
  validation. Sites on generic TLDs (`.com`) with a local-format number and
  no `+` prefix will validate as `None` — raw value is still preserved.
- CAPTCHA detection is not implemented; such pages will simply surface as
  `HTTP_ERROR`, `BLOCKED`, or `INSUFFICIENT_CONTENT` depending on server
  behavior.
- Persistence uses PostgreSQL-specific `INSERT ... ON CONFLICT` upserts
  (`sqlalchemy.dialects.postgresql`) and has only been validated schema-wise
  against SQLite in this environment (no live Postgres/Supabase instance was
  available) — verify against a real `DATABASE_URL` before relying on it.
- The observation `UniqueConstraint` used for dedup on insert does not
  collapse rows where `normalized_value IS NULL` (Postgres treats each NULL
  as distinct), so ambiguous phone/address observations can accumulate
  duplicate rows across repeated crawls of the same page.
- Requests to a domain are made sequentially with a single retry, no
  exponential backoff or per-domain rate limiting yet (Sprint 3 scope).

## Integration contract (for the ChatGPT orchestration agent)

Call conceptually as `crawl_company(website, max_pages)`. This service
returns facts and evidence only — normalized text, structured contact
observations with provenance, and page-level status. It performs no
classification, scoring, or commercial interpretation; that reasoning stays
in the orchestration agent.
