"""Postgres查询性能分析子代理.

负责分析查询执行计划、识别性能问题和提供优化建议。
"""

from __future__ import annotations

import json
import re
from typing import Any

from deepagents import SubAgent
from langchain_core.tools import tool


# ============================================================================
# 查询分析工具
# ============================================================================


@tool
def parse_query_plan(explain_plan: str) -> dict[str, Any]:
    """解析EXPLAIN ANALYZE输出，提取性能指标.

    Args:
        explain_plan: EXPLAIN ANALYZE的输出结果

    Returns:
        包含性能指标的字典
    """
    lines = explain_plan.strip().split('\n')

    metrics = {
        'total_cost': None,
        'startup_cost': None,
        'execution_time': None,
        'planning_time': None,
        'rows_estimated': None,
        'rows_actual': None,
        'node_types': [],
        'sequential_scans': 0,
        'index_scans': 0,
        'joins': [],
        'has_sort': False,
    }

    # 提取成本和时间信息
    for line in lines:
        if 'Total cost' in line or 'total cost' in line:
            match = re.search(r'(\d+\.\d+)\.\.(\d+\.\d+)', line)
            if match:
                metrics['startup_cost'] = float(match.group(1))
                metrics['total_cost'] = float(match.group(2))

        if 'Execution Time' in line or 'execution time' in line:
            match = re.search(r'(\d+\.\d+)\s*ms', line)
            if match:
                metrics['execution_time'] = float(match.group(1))

        if 'Planning Time' in line or 'planning time' in line:
            match = re.search(r'(\d+\.\d+)\s*ms', line)
            if match:
                metrics['planning_time'] = float(match.group(1))

        if 'rows=' in line.lower():
            match = re.search(r'rows=(\d+)', line.lower())
            if match:
                metrics['rows_estimated'] = int(match.group(1))

        if 'Seq Scan' in line:
            metrics['sequential_scans'] += 1
            metrics['node_types'].append('Seq Scan')

        if 'Index Scan' in line:
            metrics['index_scans'] += 1
            metrics['node_types'].append('Index Scan')

        if 'Join' in line or 'join' in line:
            metrics['joins'].append(line.strip())

        if 'Sort' in line:
            metrics['has_sort'] = True

    return metrics


@tool
def identify_slow_patterns(query: str, execution_time_ms: float = 0) -> dict[str, Any]:
    """识别查询中的常见性能问题模式.

    Args:
        query: SQL查询语句
        execution_time_ms: 执行时间（毫秒）

    Returns:
        包含问题模式和优化建议的字典
    """
    issues = []
    suggestions = []

    query_upper = query.upper()

    # 检查SELECT *
    if 'SELECT *' in query_upper:
        issues.append({
            'type': 'SELECT *',
            'severity': 'MEDIUM',
            'description': '查询使用SELECT *可能获取不必要的列'
        })
        suggestions.append('只选择需要的列，减少数据传输')

    # 检查多个JOIN
    join_count = query_upper.count('JOIN')
    if join_count > 3:
        issues.append({
            'type': 'MULTIPLE_JOINS',
            'severity': 'MEDIUM',
            'description': f'查询包含 {join_count} 个JOIN操作，可能导致性能问题'
        })
        suggestions.append('考虑优化JOIN顺序或使用物化视图')

    # 检查LIKE通配符在前面
    if "LIKE '%'" in query_upper or "LIKE '%%" in query_upper:
        issues.append({
            'type': 'LEADING_WILDCARD',
            'severity': 'HIGH',
            'description': '使用前导通配符的LIKE会导致全表扫描'
        })
        suggestions.append('避免使用前导通配符，考虑使用全文搜索或ILIKE')

    # 检查NOT IN
    if 'NOT IN' in query_upper:
        issues.append({
            'type': 'NOT_IN',
            'severity': 'MEDIUM',
            'description': 'NOT IN可能无法利用索引'
        })
        suggestions.append('考虑使用NOT EXISTS替代NOT IN')

    # 检查HAVING
    if 'HAVING' in query_upper and 'WHERE' not in query_upper:
        issues.append({
            'type': 'HAVING_WITHOUT_WHERE',
            'severity': 'MEDIUM',
            'description': '缺少WHERE子句会导致全表扫描'
        })
        suggestions.append('添加WHERE子句以减少分组前的行数')

    # 检查子查询
    subquery_count = query.count('(SELECT') + query.count('(select')
    if subquery_count > 2:
        issues.append({
            'type': 'MULTIPLE_SUBQUERIES',
            'severity': 'MEDIUM',
            'description': f'查询包含 {subquery_count} 个子查询'
        })
        suggestions.append('考虑使用CTE或JOIN替代多个子查询')

    # 检查执行时间
    if execution_time_ms > 1000:
        issues.append({
            'type': 'SLOW_EXECUTION',
            'severity': 'HIGH',
            'description': f'查询执行时间 {execution_time_ms:.0f}ms，超过1秒'
        })
        suggestions.append('检查EXPLAIN ANALYZE输出，寻找瓶颈节点')

    return {
        'total_issues': len(issues),
        'issues': issues,
        'suggestions': suggestions,
        'severity_summary': {
            'HIGH': len([i for i in issues if i['severity'] == 'HIGH']),
            'MEDIUM': len([i for i in issues if i['severity'] == 'MEDIUM']),
            'LOW': len([i for i in issues if i['severity'] == 'LOW']),
        }
    }


@tool
def recommend_optimizations(
    query: str,
    execution_time_ms: float,
    node_types: list[str] | None = None
) -> dict[str, Any]:
    """为查询提供优化建议.

    Args:
        query: SQL查询语句
        execution_time_ms: 执行时间（毫秒）
        node_types: 执行计划中的节点类型列表

    Returns:
        包含优化建议的字典
    """
    recommendations = []
    priority_optimizations = []

    if node_types is None:
        node_types = []

    # 顺序扫描优化
    if 'Seq Scan' in node_types and len(node_types) > 1:
        recommendations.append({
            'priority': 'HIGH',
            'optimization': '添加索引',
            'reason': '存在顺序扫描，可通过创建索引改进',
            'example': 'CREATE INDEX idx_column ON table(column);'
        })
        priority_optimizations.append('添加索引')

    # 内存和排序优化
    if execution_time_ms > 5000:
        recommendations.append({
            'priority': 'HIGH',
            'optimization': '增加work_mem',
            'reason': '查询执行时间很长，可能需要更多内存用于排序',
            'example': 'SET work_mem = "256MB";'
        })
        priority_optimizations.append('调整work_mem参数')

    # 统计信息更新
    recommendations.append({
        'priority': 'MEDIUM',
        'optimization': '更新表统计信息',
        'reason': '优化器需要准确的统计信息来制定执行计划',
        'example': 'ANALYZE table_name;'
    })

    # 查询改写
    if 'JOIN' in query.upper():
        recommendations.append({
            'priority': 'MEDIUM',
            'optimization': '优化JOIN顺序',
            'reason': 'JOIN顺序会影响执行效率',
            'example': '重新排序JOIN，将更小的结果集放在前面'
        })

    # 并行查询
    if execution_time_ms > 2000:
        recommendations.append({
            'priority': 'MEDIUM',
            'optimization': '启用并行查询',
            'reason': '长时间运行的查询可以从并行执行中受益',
            'example': 'SET max_parallel_workers_per_gather = 4;'
        })
        priority_optimizations.append('启用并行执行')

    return {
        'total_recommendations': len(recommendations),
        'priority_optimizations': priority_optimizations,
        'recommendations': sorted(
            recommendations,
            key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}.get(x['priority'], 3)
        ),
        'estimated_improvement': {
            'optimistic': f'{execution_time_ms * 0.5:.0f}ms (50% 改进)',
            'realistic': f'{execution_time_ms * 0.7:.0f}ms (30% 改进)',
            'description': '实际改进取决于具体优化和数据分布'
        }
    }


# ============================================================================
# 子代理定义
# ============================================================================


def create_query_analyzer_agent() -> SubAgent:
    """创建查询分析子代理.

    Returns:
        配置好的SubAgent实例
    """
    return SubAgent(
        name="query_analyzer",
        description="分析Postgres查询性能，识别问题并提供优化建议",
        system_prompt="""你是一个Postgres查询优化专家。你的任务是：
1. 接收SQL查询和EXPLAIN ANALYZE输出
2. 使用查询分析工具来分析执行计划
3. 识别性能瓶颈和常见问题模式
4. 提供具体的优化建议

分析重点：
- 查询成本（startup_cost, total_cost）
- 执行时间和规划时间
- 扫描类型（顺序扫描vs索引扫描）
- JOIN操作的效率
- 排序和聚合操作

优化建议应该是：
- 优先级明确（HIGH/MEDIUM/LOW）
- 具体可操作（包含SQL示例）
- 估计改进效果

始终保持回答简洁准确。""",
        tools=[
            parse_query_plan,
            identify_slow_patterns,
            recommend_optimizations,
        ]
    )


# 导出子代理实例供 __init__.py 使用
query_analyzer_agent = create_query_analyzer_agent()
