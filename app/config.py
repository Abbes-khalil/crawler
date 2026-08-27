import os

from dotenv import load_dotenv

from app.paths import default_database_url

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")

CRAWLER_USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "ASBizDevCrawler/0.1",
)

DEFAULT_MAX_PAGES = int(
    os.getenv("DEFAULT_MAX_PAGES", "5")
)

REQUEST_TIMEOUT = float(
    os.getenv("REQUEST_TIMEOUT", "15")
)

REQUEST_RETRY_COUNT = int(
    os.getenv("REQUEST_RETRY_COUNT", "1")
)

RESPECT_ROBOTS_TXT = os.getenv(
    "RESPECT_ROBOTS_TXT", "true"
).lower() == "true"

SITEMAP_MAX_URLS = int(
    os.getenv("SITEMAP_MAX_URLS", "200")
)

PLAYWRIGHT_ENABLED = os.getenv(
    "PLAYWRIGHT_ENABLED", "true"
).lower() == "true"

PLAYWRIGHT_MIN_CONTENT_CHARS = int(
    os.getenv("PLAYWRIGHT_MIN_CONTENT_CHARS", "200")
)

PLAYWRIGHT_TIMEOUT_MS = int(
    os.getenv("PLAYWRIGHT_TIMEOUT_MS", "15000")
)

# Local-first: defaults to a SQLite file in the per-user app-data directory.
# A full DATABASE_URL (e.g. Postgres) may still be supplied to override it.
DATABASE_URL = os.getenv("DATABASE_URL") or default_database_url()

# Local HTTP server. Binds to loopback only - never exposed to the LAN.
HOST = os.getenv("HOST", "127.0.0.1")
PREFERRED_PORT = int(os.getenv("PREFERRED_PORT", "8765"))

MAX_CRAWL_PAGES = int(os.getenv("MAX_CRAWL_PAGES", "20"))

# The frontend is served from the same origin as the API in production, so
# CORS is normally unnecessary. These origins stay allow-listed for running
# the Next.js dev server against a separately launched backend.
DEFAULT_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

_frontend_origin_env = os.getenv("FRONTEND_ORIGIN")
FRONTEND_ORIGINS = (
    [origin.strip() for origin in _frontend_origin_env.split(",") if origin.strip()]
    if _frontend_origin_env
    else DEFAULT_FRONTEND_ORIGINS
)
