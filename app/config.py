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