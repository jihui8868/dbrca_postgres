"""RCA API路由.

处理HTTP请求的主要业务逻辑。
"""

from __future__ import annotations

from datetime import datetime
import uuid
import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    RCASessionCreate,
    RCASessionResponse,
    LogAnalysisRequest,
    LogAnalysisResponse,
    QueryAnalysisRequest,
    QueryAnalysisResponse,
    MetricsAnalysisRequest,
    MetricsAnalysisResponse,
    RCAReportRequest,
    RCAReportResponse,
    HealthCheckResponse,
)
from app.agents.main_agent import build_main_agent
from app.agents.subagents.log_analyzer import (
    parse_postgres_log,
    extract_errors,
    analyze_log_patterns,
    summarize_issues,
)
from app.agents.subagents.query_analyzer import (
    parse_query_plan,
    identify_slow_patterns,
    recommend_optimizations,
)
from app.agents.subagents.metrics_analyzer import (
    analyze_cache_hit_ratio,
    analyze_connection_stats,
    analyze_disk_io,
    analyze_lock_contention,
    generate_health_report,
)
from app.agents.subagents.report_gen import (
    summarize_findings,
    format_markdown_report,
    format_html_report,
    create_action_plan,
)

_logger = logging.getLogger("api.rca")

# 创建API路由
rca_router = APIRouter(prefix="/api/rca", tags=["RCA"])

# 简单的内存存储（生产环境应使用数据库）
_sessions: dict[str, dict] = {}
_analyses: dict[str, dict] = {}


# ============================================================================
# 会话管理
# ============================================================================


@rca_router.post("/sessions", response_model=RCASessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(req: RCASessionCreate) -> RCASessionResponse:
    """创建RCA分析会话."""
    session_id = uuid.uuid4().hex[:16]
    now = datetime.utcnow()

    session = {
        'id': session_id,
        'created_at': now,
        'updated_at': now,
        'status': 'active',
        'description': req.description,
        'db_host': req.db_host,
        'db_port': req.db_port,
    }

    _sessions[session_id] = session
    _logger.info(f"创建RCA会话: {session_id}")

    return RCASessionResponse(**session)


@rca_router.get("/sessions/{session_id}", response_model=RCASessionResponse)
def get_session(session_id: str) -> RCASessionResponse:
    """获取会话信息."""
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在"
        )

    return RCASessionResponse(**_sessions[session_id])


# ============================================================================
# 日志分析
# ============================================================================


@rca_router.post("/logs/analyze", response_model=LogAnalysisResponse)
def analyze_logs(req: LogAnalysisRequest) -> LogAnalysisResponse:
    """分析Postgres日志."""
    if req.session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {req.session_id} 不存在"
        )

    try:
        # 使用日志分析工具
        parsed = parse_postgres_log.invoke({"log_content": req.log_content})
        errors = extract_errors.invoke({"log_content": req.log_content, "severity": "ERROR"})
        patterns = analyze_log_patterns.invoke({"log_content": req.log_content})
        issues = summarize_issues.invoke({"log_content": req.log_content, "error_threshold": 2})

        analysis_id = uuid.uuid4().hex[:16]
        now = datetime.utcnow()

        result = {
            'id': analysis_id,
            'session_id': req.session_id,
            'created_at': now,
            'total_entries': parsed.get('total_entries', 0),
            'error_count': errors.get('error_count', 0),
            'warning_count': 0,
            'issues_found': len(issues.get('identified_issues', [])),
            'analysis_result': {
                'parsed': parsed,
                'errors': errors,
                'patterns': patterns,
                'issues': issues,
            }
        }

        _analyses[analysis_id] = result
        _logger.info(f"日志分析完成: {analysis_id}, 发现 {result['issues_found']} 个问题")

        return LogAnalysisResponse(**result)

    except Exception as e:
        _logger.error(f"日志分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"日志分析失败: {str(e)}"
        )


# ============================================================================
# 查询分析
# ============================================================================


@rca_router.post("/queries/analyze", response_model=QueryAnalysisResponse)
def analyze_query(req: QueryAnalysisRequest) -> QueryAnalysisResponse:
    """分析SQL查询性能."""
    if req.session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {req.session_id} 不存在"
        )

    try:
        plan_analysis = {}
        if req.explain_plan:
            plan_analysis = parse_query_plan.invoke({"explain_plan": req.explain_plan})

        slow_patterns = identify_slow_patterns.invoke({
            "query": req.query,
            "execution_time_ms": req.execution_time_ms or 0
        })

        recommendations = recommend_optimizations.invoke({
            "query": req.query,
            "execution_time_ms": req.execution_time_ms or 0,
            "node_types": plan_analysis.get('node_types', [])
        })

        analysis_id = uuid.uuid4().hex[:16]
        now = datetime.utcnow()

        result = {
            'id': analysis_id,
            'session_id': req.session_id,
            'created_at': now,
            'query': req.query,
            'execution_time_ms': req.execution_time_ms,
            'total_cost': plan_analysis.get('total_cost'),
            'issues_found': slow_patterns.get('total_issues', 0),
            'analysis_result': {
                'plan': plan_analysis,
                'patterns': slow_patterns,
                'recommendations': recommendations,
            }
        }

        _analyses[analysis_id] = result
        _logger.info(f"查询分析完成: {analysis_id}, 发现 {result['issues_found']} 个问题")

        return QueryAnalysisResponse(**result)

    except Exception as e:
        _logger.error(f"查询分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询分析失败: {str(e)}"
        )


# ============================================================================
# 性能指标分析
# ============================================================================


@rca_router.post("/metrics/analyze", response_model=MetricsAnalysisResponse)
def analyze_metrics(req: MetricsAnalysisRequest) -> MetricsAnalysisResponse:
    """分析数据库性能指标."""
    if req.session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {req.session_id} 不存在"
        )

    try:
        analysis_results = {}

        # 缓存分析
        if req.cache_hit_ratio is not None:
            analysis_results['cache'] = analyze_cache_hit_ratio.invoke({
                "heap_blks_read": int((100 - req.cache_hit_ratio) / req.cache_hit_ratio * 1000),
                "heap_blks_hit": int(req.cache_hit_ratio / (100 - req.cache_hit_ratio) * 1000)
            })

        # 连接分析
        if req.active_connections is not None and req.max_connections is not None:
            idle_conn = req.max_connections - req.active_connections
            analysis_results['connections'] = analyze_connection_stats.invoke({
                "active_connections": req.active_connections,
                "idle_connections": max(0, idle_conn),
                "max_connections": req.max_connections
            })

        # 磁盘IO分析
        if req.seq_scan_percent is not None:
            analysis_results['io'] = analyze_disk_io.invoke({
                "seq_scan_count": int(req.seq_scan_percent * 10),
                "index_scan_count": int((100 - req.seq_scan_percent) * 10),
                "random_io_ms": 5.0,
                "seq_io_ms": 3.0
            })

        # 整体健康评分
        health = generate_health_report.invoke({
            "cache_hit_ratio": req.cache_hit_ratio or 90,
            "connection_utilization": req.connection_utilization or 50,
            "seq_scan_percent": req.seq_scan_percent or 20,
            "lock_contention": 5.0
        })

        analysis_id = uuid.uuid4().hex[:16]
        now = datetime.utcnow()

        result = {
            'id': analysis_id,
            'session_id': req.session_id,
            'created_at': now,
            'cache_hit_ratio': req.cache_hit_ratio,
            'connection_utilization': req.connection_utilization,
            'seq_scan_percent': req.seq_scan_percent,
            'health_score': health.get('overall_score', 0),
            'analysis_result': {
                'cache': analysis_results.get('cache'),
                'connections': analysis_results.get('connections'),
                'io': analysis_results.get('io'),
                'health': health,
            }
        }

        _analyses[analysis_id] = result
        _logger.info(f"指标分析完成: {analysis_id}, 健康分数: {result['health_score']}")

        return MetricsAnalysisResponse(**result)

    except Exception as e:
        _logger.error(f"指标分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"指标分析失败: {str(e)}"
        )


# ============================================================================
# RCA报告生成
# ============================================================================


@rca_router.post("/reports/generate", response_model=RCAReportResponse)
def generate_report(req: RCAReportRequest) -> RCAReportResponse:
    """生成RCA分析报告."""
    if req.session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {req.session_id} 不存在"
        )

    try:
        # 收集会话的所有分析结果
        session_analyses = {
            k: v for k, v in _analyses.items()
            if v['session_id'] == req.session_id
        }

        # 整合分析结果
        log_findings = next(
            (a['analysis_result'] for a in session_analyses.values() if 'patterns' in a.get('analysis_result', {})),
            None
        )
        query_findings = next(
            (a['analysis_result'] for a in session_analyses.values() if 'plan' in a.get('analysis_result', {})),
            None
        )
        metrics_findings = next(
            (a['analysis_result'] for a in session_analyses.values() if 'health' in a.get('analysis_result', {})),
            None
        )

        # 生成汇总
        findings_summary = summarize_findings.invoke({
            "log_findings": log_findings,
            "query_findings": query_findings,
            "metrics_findings": metrics_findings
        })

        # 生成Markdown报告
        markdown_report = format_markdown_report.invoke({
            "title": f"Postgres RCA分析报告 - {req.session_id[:8]}",
            "summary": findings_summary.get('summary', '未检测到问题'),
            "issues": findings_summary.get('root_causes', []),
            "recommendations": [],
            "metrics": findings_summary.get('impact_assessment', {})
        })

        # 生成HTML报告
        html_report = format_html_report.invoke({
            "title": f"Postgres RCA分析报告 - {req.session_id[:8]}",
            "summary": findings_summary.get('summary', '未检测到问题'),
            "issues": findings_summary.get('root_causes', []),
            "recommendations": []
        })

        # 生成行动计划
        action_plan = create_action_plan.invoke({
            "issues": findings_summary.get('root_causes', []),
            "recommendations": []
        })

        report_id = uuid.uuid4().hex[:16]
        now = datetime.utcnow()

        result = {
            'id': report_id,
            'session_id': req.session_id,
            'created_at': now,
            'title': f"Postgres RCA分析报告 - {req.session_id[:8]}",
            'summary': findings_summary.get('summary', ''),
            'root_causes': findings_summary.get('root_causes', []),
            'recommendations': [],
            'action_plan': action_plan,
            'markdown_content': markdown_report,
            'html_content': html_report,
        }

        _sessions[req.session_id]['status'] = 'completed'
        _logger.info(f"RCA报告生成完成: {report_id}")

        return RCAReportResponse(**result)

    except Exception as e:
        _logger.error(f"报告生成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}"
        )


# ============================================================================
# 健康检查
# ============================================================================


@rca_router.get("/health", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    """API健康检查."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0"
    )


__all__ = ["rca_router"]
