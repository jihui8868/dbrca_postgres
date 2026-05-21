"""数据库模型.

定义RCA系统的数据模型。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Float, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy基类."""
    pass


class RCASession(Base):
    """RCA分析会话."""

    __tablename__ = "rca_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, completed, failed
    description: Mapped[Optional[str]] = mapped_column(String(500))
    db_host: Mapped[Optional[str]] = mapped_column(String(255))
    db_port: Mapped[Optional[int]] = mapped_column(Integer, default=5432)


class LogAnalysis(Base):
    """日志分析结果."""

    __tablename__ = "log_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    total_entries: Mapped[int] = mapped_column(Integer)
    error_count: Mapped[int] = mapped_column(Integer)
    warning_count: Mapped[int] = mapped_column(Integer)

    analysis_result: Mapped[Optional[dict]] = mapped_column(JSON)
    issues_found: Mapped[int] = mapped_column(Integer, default=0)


class QueryAnalysis(Base):
    """查询分析结果."""

    __tablename__ = "query_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    query: Mapped[Optional[str]] = mapped_column(Text)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    total_cost: Mapped[Optional[float]] = mapped_column(Float)

    analysis_result: Mapped[Optional[dict]] = mapped_column(JSON)
    issues_found: Mapped[int] = mapped_column(Integer, default=0)


class MetricsAnalysis(Base):
    """性能指标分析结果."""

    __tablename__ = "metrics_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cache_hit_ratio: Mapped[Optional[float]] = mapped_column(Float)
    connection_utilization: Mapped[Optional[float]] = mapped_column(Float)
    seq_scan_percent: Mapped[Optional[float]] = mapped_column(Float)

    analysis_result: Mapped[Optional[dict]] = mapped_column(JSON)
    health_score: Mapped[Optional[float]] = mapped_column(Float)


class RCAReport(Base):
    """RCA分析报告."""

    __tablename__ = "rca_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)

    root_causes: Mapped[Optional[dict]] = mapped_column(JSON)
    recommendations: Mapped[Optional[dict]] = mapped_column(JSON)
    action_plan: Mapped[Optional[dict]] = mapped_column(JSON)

    markdown_content: Mapped[Optional[str]] = mapped_column(Text)
    html_content: Mapped[Optional[str]] = mapped_column(Text)


__all__ = [
    "Base",
    "RCASession",
    "LogAnalysis",
    "QueryAnalysis",
    "MetricsAnalysis",
    "RCAReport",
]
