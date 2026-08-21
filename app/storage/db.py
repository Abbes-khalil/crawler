from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    canonical_url = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    pages = relationship(
        "Page", back_populates="company", cascade="all, delete-orphan"
    )
    observations = relationship(
        "ObservationRecord",
        back_populates="company",
        cascade="all, delete-orphan",
    )


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True)
    company_id = Column(ForeignKey("companies.id"), nullable=False)

    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    language = Column(String, nullable=True)
    text = Column(Text, nullable=False, default="")
    status_code = Column(Integer, nullable=True)
    crawl_method = Column(String, nullable=False, default="http")
    content_hash = Column(String, nullable=False)
    crawled_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    company = relationship("Company", back_populates="pages")

    __table_args__ = (
        UniqueConstraint("company_id", "url", name="uq_company_page_url"),
    )


class ObservationRecord(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True)
    company_id = Column(ForeignKey("companies.id"), nullable=False)

    field = Column(String, nullable=False)
    raw_value = Column(String, nullable=False)
    normalized_value = Column(String, nullable=True)
    source_url = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    confidence = Column(Float, nullable=False)

    company = relationship("Company", back_populates="observations")

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "field",
            "normalized_value",
            "raw_value",
            "source_type",
            name="uq_company_observation",
        ),
    )


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(String, primary_key=True)

    status = Column(String, nullable=False, default="QUEUED")
    total_companies = Column(Integer, nullable=False, default=0)
    completed_companies = Column(Integer, nullable=False, default=0)
    failed_companies = Column(Integer, nullable=False, default=0)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    companies = relationship(
        "BatchJobCompany",
        back_populates="batch_job",
        cascade="all, delete-orphan",
    )


class BatchJobCompany(Base):
    __tablename__ = "batch_job_companies"

    id = Column(Integer, primary_key=True)
    batch_job_id = Column(ForeignKey("batch_jobs.id"), nullable=False)

    website = Column(String, nullable=False)
    status = Column(String, nullable=False, default="QUEUED")
    crawl_status = Column(String, nullable=True)
    canonical_url = Column(String, nullable=True)
    pages_crawled = Column(Integer, nullable=True)
    observations_count = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    batch_job = relationship("BatchJob", back_populates="companies")


_engine = None
_SessionLocal: sessionmaker | None = None


def is_persistence_enabled() -> bool:
    return bool(DATABASE_URL)


def get_engine():
    global _engine

    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    return _engine


def get_session() -> Session:
    global _SessionLocal

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())

    return _SessionLocal()


def create_all_tables():
    Base.metadata.create_all(get_engine())
