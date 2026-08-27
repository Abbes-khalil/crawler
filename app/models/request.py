import ipaddress
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from app.config import MAX_CRAWL_PAGES

_BLOCKED_HOSTNAMES = {"localhost", "ip6-localhost", "ip6-loopback"}


def _is_blocked_host(host: str) -> bool:
    host = host.strip().lower().strip(".")
    if not host:
        return True
    if host in _BLOCKED_HOSTNAMES:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    # Refuse to crawl loopback / link-local / private / reserved ranges:
    # the API is reachable from the local machine and must not be turned
    # into an SSRF pivot against the user's own network.
    return (
        ip.is_loopback
        or ip.is_link_local
        or ip.is_private
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


class CrawlCompanyRequest(BaseModel):
    website: str
    max_pages: int = Field(default=5, ge=1, le=MAX_CRAWL_PAGES)

    @field_validator("website")
    @classmethod
    def website_must_be_valid(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("website must not be blank")

        candidate = value if "://" in value else f"https://{value}"
        parsed = urlparse(candidate)

        if parsed.scheme not in ("http", "https"):
            raise ValueError("website must use http or https")

        host = parsed.hostname or ""
        if "." not in host and host.lower() not in _BLOCKED_HOSTNAMES:
            raise ValueError("website must be a fully-qualified domain")

        if _is_blocked_host(host):
            raise ValueError("crawling local or private-network hosts is not allowed")

        return value
