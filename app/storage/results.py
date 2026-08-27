"""Read-side queries over persisted crawl results."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.storage.db import Company, ObservationRecord, Page


def list_results(session: Session) -> list[dict]:
    page_counts = (
        select(Page.company_id, func.count(Page.id).label("n"))
        .group_by(Page.company_id)
        .subquery()
    )
    obs_counts = (
        select(
            ObservationRecord.company_id,
            func.count(ObservationRecord.id).label("n"),
        )
        .group_by(ObservationRecord.company_id)
        .subquery()
    )

    rows = session.execute(
        select(
            Company.id,
            Company.canonical_url,
            Company.created_at,
            func.coalesce(page_counts.c.n, 0),
            func.coalesce(obs_counts.c.n, 0),
        )
        .join(page_counts, page_counts.c.company_id == Company.id, isouter=True)
        .join(obs_counts, obs_counts.c.company_id == Company.id, isouter=True)
        .order_by(Company.created_at.desc())
    ).all()

    return [
        {
            "id": row[0],
            "canonical_url": row[1],
            "crawled_at": row[2].isoformat() if row[2] else None,
            "pages_count": row[3],
            "observations_count": row[4],
        }
        for row in rows
    ]


def get_result(session: Session, company_id: int) -> dict | None:
    company = session.get(Company, company_id)
    if company is None:
        return None

    pages = session.execute(
        select(Page).where(Page.company_id == company_id).order_by(Page.url)
    ).scalars().all()
    observations = session.execute(
        select(ObservationRecord)
        .where(ObservationRecord.company_id == company_id)
        .order_by(ObservationRecord.field)
    ).scalars().all()

    return {
        "id": company.id,
        "canonical_url": company.canonical_url,
        "crawled_at": company.created_at.isoformat() if company.created_at else None,
        "pages": [
            {
                "url": p.url,
                "title": p.title,
                "meta_description": p.meta_description,
                "language": p.language,
                "text": p.text,
                "status_code": p.status_code,
                "crawl_method": p.crawl_method,
                "content_hash": p.content_hash,
            }
            for p in pages
        ],
        "observations": [
            {
                "field": o.field,
                "raw_value": o.raw_value,
                "normalized_value": o.normalized_value,
                "source_url": o.source_url,
                "source_type": o.source_type,
                "observed_at": o.observed_at.isoformat() if o.observed_at else None,
                "confidence": o.confidence,
            }
            for o in observations
        ],
    }
