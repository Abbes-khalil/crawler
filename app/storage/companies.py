from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.db import Company


def get_or_create_company(session: Session, canonical_url: str) -> Company:
    existing = session.execute(
        select(Company).where(Company.canonical_url == canonical_url)
    ).scalar_one_or_none()

    if existing is not None:
        return existing

    company = Company(canonical_url=canonical_url)
    session.add(company)
    session.flush()

    return company
