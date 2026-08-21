from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Observation(BaseModel):
    field: str
    raw_value: str
    normalized_value: str | None = None
    source_url: str
    source_type: str
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    confidence: float
