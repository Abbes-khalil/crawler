"""Render a crawl result as a plain Markdown block.

The hosted single-page tool returns this text verbatim so a non-technical
user can copy it straight into an LLM / ChatGPT agent. It is intentionally
self-contained: a header with provenance, extracted contact details grouped
by field, then the readable text of each crawled page.
"""

from __future__ import annotations

from app.models.observation import Observation
from app.models.response import CrawlCompanyResponse

# Nicer section titles for the observation fields we know about; anything
# else falls back to a title-cased version of the raw field name.
_FIELD_TITLES = {
    "email": "Emails",
    "phone": "Phones",
    "address": "Addresses",
    "social": "Social links",
    "social_link": "Social links",
}


def _field_title(field: str) -> str:
    return _FIELD_TITLES.get(field, field.replace("_", " ").title())


def _observation_line(obs: Observation) -> str:
    value = obs.normalized_value or obs.raw_value
    return f"- {value}  (confidence {obs.confidence:.2f}, from {obs.source_url})"


def _observations_section(observations: list[Observation]) -> list[str]:
    if not observations:
        return ["## Contact details", "", "_None found._"]

    # Preserve first-seen order of fields for stable output.
    fields: list[str] = []
    for obs in observations:
        if obs.field not in fields:
            fields.append(obs.field)

    lines = ["## Contact details", ""]
    for field in fields:
        lines.append(f"### {_field_title(field)}")
        for obs in observations:
            if obs.field == field:
                lines.append(_observation_line(obs))
        lines.append("")
    return lines


def _pages_section(response: CrawlCompanyResponse) -> list[str]:
    if not response.pages:
        return ["## Pages", "", "_No page content could be extracted._"]

    lines = ["## Pages", ""]
    for page in response.pages:
        heading = page.url
        if page.title:
            heading = f"{page.url} — {page.title}"
        lines.append(f"### {heading}")
        text = page.text.strip()
        lines.append(text if text else "_(no readable text)_")
        lines.append("")
    return lines


def to_markdown(response: CrawlCompanyResponse) -> str:
    """Return a copy-pasteable Markdown summary of a crawl result."""
    header = [
        f"# Web crawl: {response.canonical_url}",
        "",
        f"- Status: {response.status}",
        f"- Pages crawled: {response.pages_crawled}"
        + (f" ({response.pages_failed} failed)" if response.pages_failed else ""),
        f"- Pages discovered: {response.pages_discovered}",
        f"- Duration: {response.metrics.duration_ms} ms",
        "",
    ]
    parts = header + _observations_section(response.observations)
    parts.append("")
    parts += _pages_section(response)
    return "\n".join(parts).strip() + "\n"
