from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "ok"


def test_discovery_disabled_rejects_and_does_not_scan(client: TestClient) -> None:
    response = client.post("/api/v1/discovery/jobs", json={"target_cidr": "192.168.1.0/30"})
    assert response.status_code == 403
    assert response.json()["error"] == "discovery_not_allowed"
    assert client.get("/api/v1/discovery/hosts").json() == []


def test_discovery_outside_allowlist_rejected() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.api.dependencies import get_db, get_settings_dependency
    from app.core.config import Settings
    from app.db.base import Base
    from app.main import app

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_settings() -> Settings:
        return Settings(
            discovery_enabled=True,
            authorized_discovery_cidrs=["10.10.0.0/24"],
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings_dependency] = override_settings
    try:
        with TestClient(app) as test_client:
            outside = test_client.post(
                "/api/v1/discovery/jobs", json={"target_cidr": "192.168.1.0/30"}
            )
            assert outside.status_code == 403
            assert "allowlist" in outside.json()["message"]

            malformed = test_client.post("/api/v1/discovery/jobs", json={"target_cidr": "bogus"})
            assert malformed.status_code == 403

            huge = test_client.post("/api/v1/discovery/jobs", json={"target_cidr": "10.10.0.0/8"})
            assert huge.status_code == 403
            assert test_client.get("/api/v1/discovery/hosts").json() == []
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
