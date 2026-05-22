"""RCA报告相关的数据模型."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class RCAReportRequest(BaseModel):
    """生成RCA报告的请求."""

    session_id: str
    include_log_analysis: bool = True
    include_query_analysis: bool = True
    include_metrics_analysis: bool = True


class RCAReportResponse(BaseModel):
    """RCA报告响应."""

    id: str
    session_id: str
    created_at: datetime
    title: str
    summary: str
    root_causes: Optional[list[dict[str, Any]]] = None
    recommendations: Optional[list[dict[str, Any]]] = None
    action_plan: Optional[dict[str, Any]] = None
    markdown_content: Optional[str] = None
    html_content: Optional[str] = None

    class Config:
        from_attributes = True


__all__ = [
    "RCAReportRequest",
    "RCAReportResponse",
]
