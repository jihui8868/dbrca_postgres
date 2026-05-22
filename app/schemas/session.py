"""RCA会话相关的数据模型."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RCASessionCreate(BaseModel):
    """创建RCA会话的请求."""

    description: Optional[str] = Field(None, max_length=500)
    db_host: Optional[str] = Field(None, max_length=255)
    db_port: Optional[int] = Field(default=5432, ge=1, le=65535)


class RCASessionResponse(BaseModel):
    """RCA会话响应."""

    id: str
    created_at: datetime
    updated_at: datetime
    status: str
    description: Optional[str]
    db_host: Optional[str]
    db_port: Optional[int]

    class Config:
        from_attributes = True


__all__ = [
    "RCASessionCreate",
    "RCASessionResponse",
]
