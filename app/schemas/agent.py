"""多智能体API相关的数据模型."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


# ============================================================================
# 代理查询相关
# ============================================================================


class AgentQueryRequest(BaseModel):
    """代理查询请求."""

    query: str = Field(..., min_length=1, max_length=5000, description="用户查询内容")
    session_id: Optional[str] = Field(None, description="会话ID，如果为None则生成新的")
    debug: bool = Field(False, description="是否输出调试信息")


class AgentQueryResponse(BaseModel):
    """代理查询响应."""

    session_id: str
    query: str
    response: str
    timestamp: datetime
    processing_time_ms: float


# ============================================================================
# 代理分析相关
# ============================================================================


class AnalyzeRequest(BaseModel):
    """分析请求模型."""

    query: str = Field(..., min_length=1)
    log_content: Optional[str] = None
    explain_plan: Optional[str] = None
    metrics: Optional[dict[str, Any]] = None


# ============================================================================
# 流式消息相关
# ============================================================================


class StreamMessage(BaseModel):
    """流式消息."""

    type: str  # "start", "thinking", "response", "end", "error"
    content: str
    timestamp: datetime


# ============================================================================
# 健康检查相关
# ============================================================================


class AgentHealthResponse(BaseModel):
    """代理健康检查响应."""

    status: str
    session_count: int
    agent_status: dict[str, str]
    timestamp: datetime


__all__ = [
    "AgentQueryRequest",
    "AgentQueryResponse",
    "AnalyzeRequest",
    "StreamMessage",
    "AgentHealthResponse",
]
