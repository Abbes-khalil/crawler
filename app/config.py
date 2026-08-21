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
