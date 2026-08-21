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
├── config.py             Env-driven settings (user agent, timeout, defaults)
├── api/
│   ├── crawl.py           POST /crawl-company
│   └── health.py          GET /health
├── crawler/
│   ├── orchestrator.py    Coordinates the whole crawl, builds the response
│   ├── url_normalizer.py  Scheme/host/trailing-slash/query normalization
│   ├── http_fetcher.py    Shared httpx.AsyncClient wrapper
│   ├── link_discovery.py  Same-domain link extraction from HTML
│   └── page_ranker.py     FR/EN keyword scoring + category-diverse selection
├── extraction/
│   ├── cleaner.py          Trafilatura text extraction + SHA-256 content hash
│   ├── metadata.py         title / meta description / <html lang>
│   ├── emails.py            Regex email matcher (fallback source)
│   ├── phones.py            Regex phone matcher (fallback source)
│   ├── contact_links.py     mailto:/tel: link extraction (primary source)
│   └── observations.py      Builds structured, source-aware Observation objects
└── models/
    ├── request.py    CrawlCompanyRequest
    ├── response.py   CrawlCompanyResponse, CrawlMetrics, CrawlStatus
    ├── page.py       CrawledPage, PageError
    └── observation.py Observation
```

Sprint 2/3 modules (`browser_fetcher.py`, `sitemap.py`, `robots.py`,
`jsonld.py`, `social_links.py`, `addresses.py`, `storage/`) are intentionally
**not** stubbed out yet — they'll be added when those sprints start, to avoid
carrying dead code.

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
    }
  ],
  "metrics": { "duration_ms": 4200, "http_pages": 5, "playwright_pages": 0 }
}
```

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
| `INSUFFICIENT_CONTENT` | Pages fetched but no readable text extracted from any |
| `ROBOTS_DENIED`, `CAPTCHA` | Reserved for Sprint 2 |

A technical crawl failure is never conflated with commercial irrelevance —
those are separate concerns owned by different layers of the system.

## Contact extraction

Extraction priority: `mailto:`/`tel:` links (confidence 1.0) → regex
fallback over visible text (confidence 0.7 for emails, 0.4 for phones).
Every fact is returned as an `Observation` with `raw_value`,
`normalized_value`, `source_url`, `source_type`, and `confidence` — never
as a bare string. Confidence reflects *extraction reliability*, not
commercial relevance.

Phone numbers are **never** auto-completed with an inferred country code.
`normalized_value` is only populated for `tel:` links that already carry
an explicit `+` prefix; everything else (including all regex-fallback
matches) is preserved as raw text with `normalized_value: null`. Proper
phone parsing/validation via `phonenumbers` is Sprint 2 scope.

## Tests

```powershell
pytest
```

Unit tests cover URL normalization, page scoring/category selection, link
discovery, email/phone regex extraction, metadata extraction, content
hashing, and observation deduplication. The integration test drives the
full `/crawl-company` endpoint against local HTML fixtures (`tests/fixtures/`)
with the network layer monkeypatched — the automated suite never depends on
live websites.

## Sprint roadmap

- **Sprint 1 (this release):** FastAPI service, URL normalization, HTTP-only
  fetch, link discovery, category-diverse page ranking/selection, Trafilatura
  cleaning, structured contact observations, content hashing, status model,
  structured page errors, unit + integration tests.
- **Sprint 2:** Playwright fallback for JS-rendered pages, `robots.txt` +
  sitemap discovery, JSON-LD/OpenGraph extraction, social links, address
  extraction, `phonenumbers`-based phone validation, PostgreSQL/Supabase
  persistence.
- **Sprint 3:** `POST /crawl-batch` + `GET /jobs/{job_id}`, Redis/RQ async
  job queue, per-domain rate limiting, retry/backoff, job history, metrics.

## Known limitations (Sprint 1)

- Phone regex fallback (confidence 0.4, `visible_text` source) can match
  numeric noise that isn't a phone number (copyright years, version
  strings). It is never normalized and always low-confidence — the
  consuming agent should treat sub-1.0-confidence phone observations as
  unverified. Root fix is the Sprint 2 `phonenumbers` integration.
- No JavaScript rendering — pages relying entirely on client-side rendering
  return `INSUFFICIENT_CONTENT` until the Playwright fallback lands.
- No `robots.txt` respect yet — deferred to Sprint 2 as specified.
- Requests to a domain are made sequentially, not rate-limited beyond that.

## Integration contract (for the ChatGPT orchestration agent)

Call conceptually as `crawl_company(website, max_pages)`. This service
returns facts and evidence only — normalized text, structured contact
observations with provenance, and page-level status. It performs no
classification, scoring, or commercial interpretation; that reasoning stays
in the orchestration agent.
