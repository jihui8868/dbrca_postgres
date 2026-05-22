"""API请求/响应schema.

定义RCA系统的API数据模型。所有BaseModel类在此统一导入和导出。
"""

from __future__ import annotations

# Session schemas
from app.schemas.session import (
    RCASessionCreate,
    RCASessionResponse,
)

# Analysis schemas
from app.schemas.analysis import (
    LogAnalysisRequest,
    LogAnalysisResponse,
    QueryAnalysisRequest,
    QueryAnalysisResponse,
    MetricsAnalysisRequest,
    MetricsAnalysisResponse,
)

# Report schemas
from app.schemas.report import (
    RCAReportRequest,
    RCAReportResponse,
)

# Agent schemas
from app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
    AnalyzeRequest,
    StreamMessage,
    AgentHealthResponse,
)

# Common schemas
from app.schemas.common import (
    ErrorResponse,
    SuccessResponse,
    HealthCheckResponse,
)

__all__ = [
    # Session
    "RCASessionCreate",
    "RCASessionResponse",
    # Analysis
    "LogAnalysisRequest",
    "LogAnalysisResponse",
    "QueryAnalysisRequest",
    "QueryAnalysisResponse",
    "MetricsAnalysisRequest",
    "MetricsAnalysisResponse",
    # Report
    "RCAReportRequest",
    "RCAReportResponse",
    # Agent
    "AgentQueryRequest",
    "AgentQueryResponse",
    "AnalyzeRequest",
    "StreamMessage",
    "AgentHealthResponse",
    # Common
    "ErrorResponse",
    "SuccessResponse",
    "HealthCheckResponse",
]
