from pydantic import BaseModel, Field, field_validator


class CrawlCompanyRequest(BaseModel):
    website: str
    max_pages: int = Field(default=5, ge=1, le=20)

    @field_validator("website")
    @classmethod
    def website_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("website must not be blank")

        return value
