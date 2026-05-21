"""Postgres日志分析子代理.

负责解析和分析Postgres错误日志，识别问题模式和潜在根因。
"""

from __future__ import annotations

import re
from typing import Any

from deepagents import SubAgent
from langchain_core.tools import tool


# ============================================================================
# 日志分析工具
# ============================================================================


@tool
def parse_postgres_log(log_content: str) -> dict[str, Any]:
    """解析Postgres日志内容，提取结构化信息.

    Args:
        log_content: 原始Postgres日志文本

    Returns:
        包含解析结果的字典，包括日志条目数、时间范围、严重级别分布等
    """
    lines = log_content.strip().split('\n')
    entries = []

    # Postgres日志通常包含: timestamp, severity, process, message
    # 示例: 2024-05-21 10:23:45.123 UTC [1234] ERROR: connection refused
    log_pattern = r'^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+(\w+)\s+(?:\[(\d+)\])?\s*(.*)$'

    severity_counts = {
        'DEBUG': 0, 'INFO': 0, 'WARNING': 0,
        'ERROR': 0, 'FATAL': 0, 'PANIC': 0
    }

    for line in lines:
        if not line.strip():
            continue

        match = re.match(log_pattern, line)
        if match:
            timestamp, severity, pid, message = match.groups()
            entries.append({
                'timestamp': timestamp,
                'severity': severity.upper(),
                'pid': pid,
                'message': message
            })

            if severity.upper() in severity_counts:
                severity_counts[severity.upper()] += 1

    # 计算时间范围
    time_range = None
    if entries:
        first_time = entries[0]['timestamp']
        last_time = entries[-1]['timestamp']
        time_range = f"{first_time} ~ {last_time}"

    return {
        'total_entries': len(entries),
        'time_range': time_range,
        'severity_distribution': severity_counts,
        'entries': entries[:100],  # 返回前100条
        'sample_errors': [e for e in entries if e['severity'] in ['ERROR', 'FATAL', 'PANIC']][:10]
    }


def _extract_errors_impl(log_content: str, severity: str = "ERROR") -> dict[str, Any]:
    """从日志中提取特定严重级别的错误信息 (实现).

    Args:
        log_content: 日志文本
        severity: 严重级别 (ERROR, FATAL, PANIC, WARNING等)

    Returns:
        包含错误信息的字典
    """
    lines = log_content.split('\n')
    errors = []
    error_types = {}

    severity = severity.upper()

    for line in lines:
        if severity in line.upper():
            errors.append(line)

            # 尝试提取错误类型 (如 "connection refused", "out of memory")
            if 'ERROR:' in line or 'FATAL:' in line or 'PANIC:' in line:
                # 提取冒号后的部分作为错误消息
                parts = re.split(r'ERROR:|FATAL:|PANIC:', line)
                if len(parts) > 1:
                    error_msg = parts[-1].strip()
                    # 提取第一个单词或短语作为错误类型
                    error_type = error_msg.split()[0] if error_msg else "unknown"
                    error_types[error_type] = error_types.get(error_type, 0) + 1

    return {
        'severity_level': severity,
        'error_count': len(errors),
        'error_types': error_types,
        'sample_errors': errors[:20],  # 返回前20条错误
        'error_type_distribution': {
            k: v for k, v in sorted(
                error_types.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    }


@tool
def extract_errors(log_content: str, severity: str = "ERROR") -> dict[str, Any]:
    """从日志中提取特定严重级别的错误信息.

    Args:
        log_content: 日志文本
        severity: 严重级别 (ERROR, FATAL, PANIC, WARNING等)

    Returns:
        包含错误信息的字典
    """
    return _extract_errors_impl(log_content, severity)


def _analyze_log_patterns_impl(log_content: str) -> dict[str, Any]:
    """分析日志中的常见模式和趋势 (实现).

    Args:
        log_content: 日志文本

    Returns:
        包含模式分析的字典
    """
    patterns = {
        'connection_issues': r'(connection refused|connection timeout|EOF detected|client closed)',
        'authentication': r'(authentication failed|invalid password|permission denied)',
        'memory': r'(out of memory|memory allocation|ENOMEM)',
        'disk': r'(disk full|no space left|ENOSPC)',
        'deadlock': r'(deadlock detected|waiting for)',
        'slow_query': r'(slow query|query duration|duration:)',
        'checkpoint': r'(checkpoint|recovery|WAL)',
        'replication': r'(replication|streaming|wal_keep)',
    }

    pattern_hits = {}

    for pattern_name, pattern_regex in patterns.items():
        matches = re.findall(pattern_regex, log_content, re.IGNORECASE)
        if matches:
            pattern_hits[pattern_name] = len(matches)

    # 找出前5个最常见的问题
    top_patterns = dict(
        sorted(pattern_hits.items(), key=lambda x: x[1], reverse=True)[:5]
    )

    return {
        'detected_patterns': pattern_hits,
        'top_issues': top_patterns,
        'pattern_count': len(pattern_hits),
        'total_pattern_matches': sum(pattern_hits.values())
    }


@tool
def analyze_log_patterns(log_content: str) -> dict[str, Any]:
    """分析日志中的常见模式和趋势.

    Args:
        log_content: 日志文本

    Returns:
        包含模式分析的字典
    """
    return _analyze_log_patterns_impl(log_content)


@tool
def summarize_issues(
    log_content: str,
    error_threshold: int = 5
) -> dict[str, Any]:
    """汇总日志中的关键问题和建议.

    Args:
        log_content: 日志文本
        error_threshold: 错误数量阈值，超过此值则认为严重

    Returns:
        包含问题摘要和建议的字典
    """
    # 获取错误统计 (直接调用函数逻辑，避免使用StructuredTool)
    errors = _extract_errors_impl(log_content, "ERROR")
    patterns = _analyze_log_patterns_impl(log_content)

    issues = []
    recommendations = []

    # 基于错误类型生成问题和建议
    error_type_dist = errors.get('error_type_distribution', {})

    for error_type, count in error_type_dist.items():
        if count >= error_threshold:
            issue = {
                'type': error_type,
                'severity': 'HIGH' if count > 10 else 'MEDIUM',
                'occurrences': count
            }
            issues.append(issue)

            # 根据错误类型生成建议
            if 'connection' in error_type.lower():
                recommendations.append({
                    'issue': error_type,
                    'action': '检查数据库连接池配置、网络连通性和服务状态'
                })
            elif 'memory' in error_type.lower():
                recommendations.append({
                    'issue': error_type,
                    'action': '增加服务器内存或优化查询以降低内存使用'
                })
            elif 'authentication' in error_type.lower():
                recommendations.append({
                    'issue': error_type,
                    'action': '检查用户认证配置、密码和权限设置'
                })

    # 基于模式生成额外建议
    top_patterns = patterns.get('top_issues', {})

    if 'deadlock' in top_patterns:
        recommendations.append({
            'issue': 'deadlock',
            'action': '分析并调整事务隔离级别和查询顺序以避免死锁'
        })

    if 'disk' in top_patterns:
        recommendations.append({
            'issue': 'disk_space',
            'action': '清理日志文件、临时表或增加磁盘空间'
        })

    return {
        'summary': {
            'total_errors': errors.get('error_count', 0),
            'critical_issues': len([i for i in issues if i['severity'] == 'HIGH']),
            'issue_types': len(issues)
        },
        'identified_issues': issues,
        'recommendations': recommendations,
        'next_steps': [
            '检查Postgres配置文件 (postgresql.conf)',
            '查看Postgres进程状态和系统资源使用情况',
            '分析应用程序连接和查询模式',
            '考虑运行 EXPLAIN ANALYZE 分析慢查询'
        ]
    }


# ============================================================================
# 子代理定义
# ============================================================================


def create_log_analyzer_agent() -> SubAgent:
    """创建日志分析子代理.

    Returns:
        配置好的SubAgent实例
    """
    return SubAgent(
        name="log_analyzer",
        description="分析Postgres错误日志，识别问题模式和潜在根因",
        system_prompt="""你是一个Postgres日志分析专家。你的任务是：
1. 接收原始的Postgres日志内容
2. 使用日志分析工具来解析和分析日志
3. 识别错误模式、性能问题和系统问题
4. 提供故障排查建议和解决方案

分析时要关注：
- 连接问题（连接拒绝、超时）
- 内存和磁盘空间问题
- 认证和权限问题
- 死锁和锁争用
- 复制和WAL相关问题
- 慢查询问题

对用户提供清晰、可操作的建议。""",
        tools=[
            parse_postgres_log,
            extract_errors,
            analyze_log_patterns,
            summarize_issues,
        ]
    )


# 导出子代理实例供 __init__.py 使用
log_analyzer_agent = create_log_analyzer_agent()
