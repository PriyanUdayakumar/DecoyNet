from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error: str
    message: str


class PageMeta(BaseModel):
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)


class PaginatedResponse(BaseModel):
    items: list[Any]
    meta: PageMeta


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
