from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.storage.db import Company, ObservationRecord


def save_observations(
    session: Session,
    company: Company,
    observations: list[Observation],
) -> None:
    for obs in observations:
        stmt = insert(ObservationRecord).values(
            company_id=company.id,
            field=obs.field,
            raw_value=obs.raw_value,
            normalized_value=obs.normalized_value,
            source_url=obs.source_url,
            source_type=obs.source_type,
            observed_at=obs.observed_at,
            confidence=obs.confidence,
        )

        stmt = stmt.on_conflict_do_nothing(
            index_elements=[
                "company_id",
                "field",
                "normalized_value",
                "raw_value",
                "source_type",
            ]
        )

        session.execute(stmt)
