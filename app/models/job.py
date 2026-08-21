from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CrawlBatchRequest(BaseModel):
    websites: list[str]
    max_pages: int = Field(default=5, ge=1, le=20)

    @field_validator("websites")
    @classmethod
    def websites_must_be_non_empty(cls, value: list[str]) -> list[str]:
        cleaned = [w.strip() for w in value if w.strip()]

        if not cleaned:
            raise ValueError("websites must contain at least one entry")

        return cleaned


class CrawlBatchResponse(BaseModel):
    job_id: str
    status: str
    total_companies: int


class BatchJobCompanyStatus(BaseModel):
    website: str
    status: str
    crawl_status: str | None = None
    canonical_url: str | None = None
    pages_crawled: int | None = None
    observations_count: int | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class BatchJobStatus(BaseModel):
    job_id: str
    status: str
    total_companies: int
    completed_companies: int
    failed_companies: int
    created_at: datetime
    completed_at: datetime | None = None
    companies: list[BatchJobCompanyStatus]
