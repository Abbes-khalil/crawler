import os

from dotenv import load_dotenv

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

DATABASE_URL = os.getenv("DATABASE_URL", "")

REDIS_URL = os.getenv("REDIS_URL", "")

RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "crawl")

JOB_RETRY_MAX = int(os.getenv("JOB_RETRY_MAX", "2"))

JOB_RETRY_INTERVALS_SECONDS = [
    int(x)
    for x in os.getenv("JOB_RETRY_INTERVALS_SECONDS", "10,60").split(",")
    if x.strip()
]

PER_DOMAIN_RATE_LIMIT_SECONDS = float(
    os.getenv("PER_DOMAIN_RATE_LIMIT_SECONDS", "2")
)

PER_DOMAIN_RATE_LIMIT_MAX_WAIT_SECONDS = float(
    os.getenv("PER_DOMAIN_RATE_LIMIT_MAX_WAIT_SECONDS", "30")
)

MAX_BATCH_WEBSITES = int(os.getenv("MAX_BATCH_WEBSITES", "100"))

DEFAULT_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    # Tauri's WebView2 origin for the packaged desktop app on Windows.
    "https://tauri.localhost",
    "http://tauri.localhost",
]

_frontend_origin_env = os.getenv("FRONTEND_ORIGIN")
FRONTEND_ORIGINS = (
    [origin.strip() for origin in _frontend_origin_env.split(",") if origin.strip()]
    if _frontend_origin_env
    else DEFAULT_FRONTEND_ORIGINS
)
