from __future__ import annotations

from functools import lru_cache
from ipaddress import ip_network

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DecoyNet"
    app_env: str = "local"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./decoynet.db"
    log_level: str = "INFO"
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"]
    )
    demo_mode: bool = False
    discovery_enabled: bool = False
    authorized_discovery_cidrs: list[str] = Field(default_factory=list)
    discovery_timeout_seconds: float = Field(default=1.0, gt=0, le=10)
    discovery_concurrency_limit: int = Field(default=16, gt=0, le=128)
    discovery_max_hosts: int = Field(default=64, gt=0, le=256)
    device_last_seen_threshold_seconds: int = Field(default=300, gt=0)
    severity_low_threshold: int = Field(default=20, ge=0, le=100)
    severity_medium_threshold: int = Field(default=45, ge=0, le=100)
    severity_high_threshold: int = Field(default=70, ge=0, le=100)

    @field_validator("cors_allowed_origins", "authorized_discovery_cidrs", mode="before")
    @classmethod
    def split_csv(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("authorized_discovery_cidrs")
    @classmethod
    def validate_cidrs(cls, value: list[str]) -> list[str]:
        for cidr in value:
            ip_network(cidr, strict=False)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
