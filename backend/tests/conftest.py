from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db, get_settings_dependency
from app.core.config import Settings
from app.db.base import Base
from app.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield db_session

    def override_settings() -> Settings:
        return Settings(
            database_url="sqlite://",
            demo_mode=True,
            discovery_enabled=False,
            authorized_discovery_cidrs=["192.168.1.0/24"],
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings_dependency] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
