import logging

from app.models.response import CrawlCompanyResponse
from app.storage.companies import get_or_create_company
from app.storage.db import create_all_tables, get_session, is_persistence_enabled
from app.storage.observations import save_observations
from app.storage.pages import save_pages


logger = logging.getLogger(__name__)

_tables_ready = False


def persist_crawl_result(response: CrawlCompanyResponse) -> None:
    """Best-effort persistence: a database problem must never fail the
    API response, since the crawl already succeeded from the caller's
    point of view. Silently does nothing if DATABASE_URL is not set."""
    if not is_persistence_enabled():
        return

    global _tables_ready

    session = None

    try:
        if not _tables_ready:
            create_all_tables()
            _tables_ready = True

        session = get_session()

        company = get_or_create_company(session, response.canonical_url)
        save_pages(session, company, response.pages)
        save_observations(session, company, response.observations)

        session.commit()
    except Exception:
        logger.exception(
            "Failed to persist crawl result for %s", response.canonical_url
        )

        if session is not None:
            session.rollback()
    finally:
        if session is not None:
            session.close()
