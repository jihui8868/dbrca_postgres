"""Postgres性能指标分析子代理.

负责分析数据库系统指标，识别性能瓶颈和异常。
"""

from __future__ import annotations

from typing import Any

from deepagents import SubAgent
from langchain_core.tools import tool


# ============================================================================
# 性能指标分析工具
# ============================================================================


@tool
def analyze_cache_hit_ratio(
    heap_blks_read: int,
    heap_blks_hit: int
) -> dict[str, Any]:
    """分析缓存命中率.

    Args:
        heap_blks_read: 从磁盘读取的块数
        heap_blks_hit: 从缓存读取的块数

    Returns:
        包含缓存分析的字典
    """
    total_blocks = heap_blks_read + heap_blks_hit

    if total_blocks == 0:
        return {
            'status': 'NO_DATA',
            'message': '暂无数据'
        }

    hit_ratio = (heap_blks_hit / total_blocks) * 100
    read_ratio = (heap_blks_read / total_blocks) * 100

    if hit_ratio >= 99:
        status = 'EXCELLENT'
        recommendation = '缓存配置优秀，无需调整'
    elif hit_ratio >= 95:
        status = 'GOOD'
        recommendation = '缓存配置良好，继续监控'
    elif hit_ratio >= 80:
        status = 'FAIR'
        recommendation = '缓存命中率可以改进，考虑增加shared_buffers'
    else:
        status = 'POOR'
        recommendation = '缓存命中率较低，建议增加shared_buffers（默认128MB）'

    return {
        'hit_ratio_percent': round(hit_ratio, 2),
        'read_ratio_percent': round(read_ratio, 2),
        'total_blocks': total_blocks,
        'status': status,
        'recommendation': recommendation,
        'tuning_suggestion': {
            'parameter': 'shared_buffers',
            'current_note': '检查postgresql.conf中的设置',
            'increase_by': '25% 或更多'
        } if hit_ratio < 95 else None
    }


@tool
def analyze_connection_stats(
    active_connections: int,
    idle_connections: int,
    max_connections: int = 100
) -> dict[str, Any]:
    """分析数据库连接状况.

    Args:
        active_connections: 活跃连接数
        idle_connections: 空闲连接数
        max_connections: 最大连接数限制

    Returns:
        包含连接分析的字典
    """
    total_connections = active_connections + idle_connections
    utilization_percent = (total_connections / max_connections) * 100
    active_percent = (active_connections / total_connections * 100) if total_connections > 0 else 0

    if utilization_percent > 80:
        status = 'CRITICAL'
        recommendation = '连接数接近上限，需要立即处理'
    elif utilization_percent > 60:
        status = 'WARNING'
        recommendation = '连接数较多，监控是否有连接泄漏'
    else:
        status = 'HEALTHY'
        recommendation = '连接数正常'

    issues = []
    if idle_connections > active_connections * 2:
        issues.append('存在过多空闲连接，可能有连接泄漏')

    if active_connections > max_connections * 0.9:
        issues.append('活跃连接接近上限，可能导致新连接被拒绝')

    return {
        'total_connections': total_connections,
        'active_connections': active_connections,
        'idle_connections': idle_connections,
        'max_connections': max_connections,
        'utilization_percent': round(utilization_percent, 2),
        'active_percent': round(active_percent, 2),
        'status': status,
        'recommendation': recommendation,
        'issues': issues,
        'tuning_suggestion': {
            'parameter': 'max_connections',
            'action': 'increase' if utilization_percent > 60 else 'none',
            'suggested_value': max(max_connections * 1.5, 200) if utilization_percent > 60 else None
        }
    }


@tool
def analyze_disk_io(
    seq_scan_count: int,
    index_scan_count: int,
    random_io_ms: float,
    seq_io_ms: float
) -> dict[str, Any]:
    """分析磁盘IO性能.

    Args:
        seq_scan_count: 顺序扫描次数
        index_scan_count: 索引扫描次数
        random_io_ms: 随机IO时间（毫秒）
        seq_io_ms: 顺序IO时间（毫秒）

    Returns:
        包含IO分析的字典
    """
    total_scans = seq_scan_count + index_scan_count

    if total_scans == 0:
        return {'status': 'NO_DATA', 'message': '暂无扫描数据'}

    seq_scan_percent = (seq_scan_count / total_scans) * 100
    index_scan_percent = (index_scan_count / total_scans) * 100

    # 分析IO性能
    if random_io_ms > 0 and seq_io_ms > 0:
        io_performance = seq_io_ms / random_io_ms if random_io_ms > 0 else 0
        if io_performance > 1:
            io_status = 'GOOD'
            io_note = '顺序IO性能优于随机IO，这是正常的'
        else:
            io_status = 'CHECK'
            io_note = '顺序IO和随机IO性能相近，可能存在问题'
    else:
        io_status = 'UNKNOWN'
        io_note = '无法确定IO性能'

    issues = []
    if seq_scan_percent > 30 and index_scan_count > 0:
        issues.append(f'顺序扫描占比{seq_scan_percent:.1f}%，超过30%，考虑添加索引')

    return {
        'scan_distribution': {
            'sequential_scans': seq_scan_count,
            'index_scans': index_scan_count,
            'seq_scan_percent': round(seq_scan_percent, 2),
            'index_scan_percent': round(index_scan_percent, 2)
        },
        'io_performance': {
            'random_io_ms': random_io_ms,
            'seq_io_ms': seq_io_ms,
            'status': io_status,
            'note': io_note
        },
        'issues': issues,
        'recommendation': 'Add indexes' if seq_scan_percent > 30 else 'Current IO pattern is acceptable'
    }


@tool
def analyze_lock_contention(
    locks_held: int,
    locks_waiting: int,
    blocked_queries: int = 0
) -> dict[str, Any]:
    """分析锁竞争状况.

    Args:
        locks_held: 持有的锁数
        locks_waiting: 等待的锁数
        blocked_queries: 被阻塞的查询数

    Returns:
        包含锁分析的字典
    """
    total_locks = locks_held + locks_waiting

    if total_locks == 0:
        return {'status': 'HEALTHY', 'message': '无锁竞争'}

    wait_ratio = (locks_waiting / total_locks) * 100 if total_locks > 0 else 0

    if blocked_queries > 10:
        status = 'CRITICAL'
        severity = 'HIGH'
    elif blocked_queries > 0:
        status = 'WARNING'
        severity = 'MEDIUM'
    else:
        status = 'HEALTHY'
        severity = 'LOW'

    issues = []
    if wait_ratio > 10:
        issues.append(f'等待锁的比例过高（{wait_ratio:.1f}%），存在锁竞争')

    if blocked_queries > 0:
        issues.append(f'{blocked_queries} 个查询被阻塞，需要检查')

    return {
        'locks_held': locks_held,
        'locks_waiting': locks_waiting,
        'blocked_queries': blocked_queries,
        'wait_ratio_percent': round(wait_ratio, 2),
        'status': status,
        'severity': severity,
        'issues': issues,
        'recommendations': [
            '检查长时间运行的事务',
            '考虑使用行级锁而不是表级锁',
            '优化事务长度，尽快提交',
            '检查是否存在死锁'
        ] if severity != 'LOW' else []
    }


@tool
def generate_health_report(
    cache_hit_ratio: float,
    connection_utilization: float,
    seq_scan_percent: float,
    lock_contention: float
) -> dict[str, Any]:
    """生成数据库健康状态报告.

    Args:
        cache_hit_ratio: 缓存命中率（0-100）
        connection_utilization: 连接利用率（0-100）
        seq_scan_percent: 顺序扫描比例（0-100）
        lock_contention: 锁竞争程度（0-100）

    Returns:
        包含健康状态评分的字典
    """
    # 计算各个维度的分数（0-100）
    cache_score = cache_hit_ratio
    connection_score = 100 - min(connection_utilization, 100)
    io_score = 100 - (seq_scan_percent * 3)  # 顺序扫描比例越低越好
    lock_score = 100 - lock_contention

    # 计算整体健康分数
    overall_score = (cache_score + connection_score + io_score + lock_score) / 4

    if overall_score >= 85:
        health_status = 'HEALTHY'
        action_required = False
    elif overall_score >= 70:
        health_status = 'FAIR'
        action_required = True
    else:
        health_status = 'POOR'
        action_required = True

    # 识别主要瓶颈
    bottlenecks = []
    if cache_score < 80:
        bottlenecks.append('缓存命中率低')
    if connection_score < 70:
        bottlenecks.append('连接数过多')
    if io_score < 70:
        bottlenecks.append('顺序扫描过多，需要优化索引')
    if lock_score < 70:
        bottlenecks.append('锁竞争严重')

    return {
        'overall_score': round(overall_score, 2),
        'health_status': health_status,
        'action_required': action_required,
        'dimension_scores': {
            'cache_hit_ratio': round(cache_score, 2),
            'connection_utilization': round(connection_score, 2),
            'io_efficiency': round(io_score, 2),
            'lock_contention': round(lock_score, 2)
        },
        'bottlenecks': bottlenecks,
        'summary': f'数据库健康状态: {health_status}。' + (
            f'主要瓶颈: {", ".join(bottlenecks)}' if bottlenecks else '运行状态良好'
        )
    }


# ============================================================================
# 子代理定义
# ============================================================================


def create_metrics_analyzer_agent() -> SubAgent:
    """创建性能指标分析子代理.

    Returns:
        配置好的SubAgent实例
    """
    return SubAgent(
        name="metrics_analyzer",
        description="分析Postgres性能指标，识别系统瓶颈",
        system_prompt="""你是一个Postgres性能分析专家。你的任务是：
1. 接收数据库性能指标（缓存、连接、IO、锁等）
2. 使用指标分析工具来评估性能状况
3. 识别系统瓶颈和异常
4. 提供具体的优化建议

分析重点：
- 缓存命中率和shared_buffers配置
- 连接数和连接池配置
- 磁盘IO模式（顺序vs随机）
- 锁竞争和死锁
- 整体数据库健康状态

优化建议应该：
- 针对具体指标
- 包含参数调整建议
- 估计改进效果

以客观数据为基础，提供清晰的诊断。""",
        tools=[
            analyze_cache_hit_ratio,
            analyze_connection_stats,
            analyze_disk_io,
            analyze_lock_contention,
            generate_health_report,
        ]
    )


# 导出子代理实例供 __init__.py 使用
metrics_analyzer_agent = create_metrics_analyzer_agent()
