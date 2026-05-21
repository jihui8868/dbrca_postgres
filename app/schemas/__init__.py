"""API请求/响应schema.

定义RCA系统的API数据模型。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


# ============================================================================
# RCA会话相关
# ============================================================================


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


# ============================================================================
# RCA报告相关
# ============================================================================


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


# ============================================================================
# 通用响应模型
# ============================================================================


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
    "RCASessionCreate",
    "RCASessionResponse",
    "LogAnalysisRequest",
    "LogAnalysisResponse",
    "QueryAnalysisRequest",
    "QueryAnalysisResponse",
    "MetricsAnalysisRequest",
    "MetricsAnalysisResponse",
    "RCAReportRequest",
    "RCAReportResponse",
    "ErrorResponse",
    "SuccessResponse",
    "HealthCheckResponse",
]
