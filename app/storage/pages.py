from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.models.page import CrawledPage
from app.storage.db import Company, Page


def save_pages(
    session: Session,
    company: Company,
    pages: list[CrawledPage],
) -> None:
    for page in pages:
        stmt = insert(Page).values(
            company_id=company.id,
            url=page.url,
            title=page.title,
            meta_description=page.meta_description,
            language=page.language,
            text=page.text,
            status_code=page.status_code,
            crawl_method=page.crawl_method,
            content_hash=page.content_hash,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["company_id", "url"],
            set_={
                "title": stmt.excluded.title,
                "meta_description": stmt.excluded.meta_description,
                "language": stmt.excluded.language,
                "text": stmt.excluded.text,
                "status_code": stmt.excluded.status_code,
                "crawl_method": stmt.excluded.crawl_method,
                "content_hash": stmt.excluded.content_hash,
            },
        )

        session.execute(stmt)
