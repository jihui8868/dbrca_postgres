"""通用的数据模型."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """错误响应."""

    code: int
    message: str
    details: Optional[dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """通用成功响应."""

    code: int = 200
    message: str
    data: Optional[dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """健康检查响应."""

    status: str
    timestamp: datetime
    version: str


__all__ = [
    "ErrorResponse",
    "SuccessResponse",
    "HealthCheckResponse",
]
