"""分析相关的数据模型."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


# ============================================================================
# 日志分析相关
# ============================================================================


class LogAnalysisRequest(BaseModel):
    """日志分析请求."""

    session_id: str
    log_content: str = Field(..., min_length=1)


class LogAnalysisResponse(BaseModel):
    """日志分析响应."""

    id: str
    session_id: str
    created_at: datetime
    total_entries: int
    error_count: int
    warning_count: int
    issues_found: int
    analysis_result: Optional[dict[str, Any]]

    class Config:
        from_attributes = True


# ============================================================================
# 查询分析相关
# ============================================================================


class QueryAnalysisRequest(BaseModel):
    """查询分析请求."""

    session_id: str
    query: str = Field(..., min_length=1)
    explain_plan: Optional[str] = None
    execution_time_ms: Optional[float] = None


class QueryAnalysisResponse(BaseModel):
    """查询分析响应."""

    id: str
    session_id: str
    created_at: datetime
    query: Optional[str]
    execution_time_ms: Optional[float]
    total_cost: Optional[float]
    issues_found: int
    analysis_result: Optional[dict[str, Any]]

    class Config:
        from_attributes = True


# ============================================================================
# 性能指标分析相关
# ============================================================================


class MetricsAnalysisRequest(BaseModel):
    """性能指标分析请求."""

    session_id: str
    cache_hit_ratio: Optional[float] = Field(None, ge=0, le=100)
    connection_utilization: Optional[float] = Field(None, ge=0, le=100)
    seq_scan_percent: Optional[float] = Field(None, ge=0, le=100)
    active_connections: Optional[int] = None
    max_connections: Optional[int] = None


class MetricsAnalysisResponse(BaseModel):
    """性能指标分析响应."""

    id: str
    session_id: str
    created_at: datetime
    cache_hit_ratio: Optional[float]
    connection_utilization: Optional[float]
    seq_scan_percent: Optional[float]
    health_score: Optional[float]
    analysis_result: Optional[dict[str, Any]]

    class Config:
        from_attributes = True


__all__ = [
    "LogAnalysisRequest",
    "LogAnalysisResponse",
    "QueryAnalysisRequest",
    "QueryAnalysisResponse",
    "MetricsAnalysisRequest",
    "MetricsAnalysisResponse",
]
