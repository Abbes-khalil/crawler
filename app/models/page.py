from pydantic import BaseModel


class CrawledPage(BaseModel):
    url: str
    title: str | None = None
    meta_description: str | None = None
    language: str | None = None
    text: str = ""
    status_code: int | None = None
    crawl_method: str = "http"
    content_hash: str = ""


class PageError(BaseModel):
    url: str
    status: str
    error: str
