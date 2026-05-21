#!/usr/bin/env python3
"""完整的RCA系统集成测试.

验证所有组件的功能和集成。
"""

from app.agents.subagents import ALL_SUBAGENTS
from app.routers import (
    create_session,
    analyze_logs,
    analyze_query,
    analyze_metrics,
    generate_report,
)
from app.schemas import (
    RCASessionCreate,
    LogAnalysisRequest,
    QueryAnalysisRequest,
    MetricsAnalysisRequest,
    RCAReportRequest,
)


def test_subagents():
    """测试所有子代理是否正确注册."""
    print("=" * 80)
    print("测试1: 子代理注册")
    print("=" * 80)

    expected_agents = ['log_analyzer', 'query_analyzer', 'metrics_analyzer', 'report_gen']
    actual_agents = [sa.get('name') for sa in ALL_SUBAGENTS]

    print(f"期望: {expected_agents}")
    print(f"实际: {actual_agents}")

    for expected in expected_agents:
        if expected not in actual_agents:
            print(f"✗ 缺少子代理: {expected}")
            return False

    print("✓ 所有子代理正确注册\n")
    return True


def test_log_analysis():
    """测试日志分析端点."""
    print("=" * 80)
    print("测试2: 日志分析")
    print("=" * 80)

    # 创建会话
    session_req = RCASessionCreate(description="测试会话")
    session = create_session(session_req)
    print(f"✓ 创建会话: {session.id}\n")

    # 分析日志
    log_content = """2024-05-21 10:23:45.123 UTC [1234] ERROR: connection refused
2024-05-21 10:23:46.456 UTC [1235] INFO: database started
2024-05-21 10:24:00.789 UTC [1236] ERROR: out of memory
2024-05-21 10:24:15.012 UTC [1237] ERROR: connection timeout"""

    log_req = LogAnalysisRequest(
        session_id=session.id,
        log_content=log_content
    )

    result = analyze_logs(log_req)
    print(f"✓ 日志分析完成")
    print(f"  - 总条目数: {result.total_entries}")
    print(f"  - 错误数: {result.error_count}")
    print(f"  - 发现问题: {result.issues_found}\n")

    return session.id


def test_query_analysis(session_id: str):
    """测试查询分析端点."""
    print("=" * 80)
    print("测试3: 查询分析")
    print("=" * 80)

    query = """SELECT * FROM users
              WHERE customer_id NOT IN (SELECT id FROM orders)
              ORDER BY created_at DESC"""

    explain_plan = """Seq Scan on users  (cost=0.00..1000.00 rows=1000 width=32)
   Filter: NOT (hashed SubPlan 1)
   SubPlan 1
     ->  Seq Scan on orders  (cost=0.00..100.00 rows=1000 width=4)"""

    query_req = QueryAnalysisRequest(
        session_id=session_id,
        query=query,
        explain_plan=explain_plan,
        execution_time_ms=2500
    )

    result = analyze_query(query_req)
    print(f"✓ 查询分析完成")
    print(f"  - 执行时间: {result.execution_time_ms}ms")
    print(f"  - 发现问题: {result.issues_found}\n")


def test_metrics_analysis(session_id: str):
    """测试性能指标分析端点."""
    print("=" * 80)
    print("测试4: 性能指标分析")
    print("=" * 80)

    metrics_req = MetricsAnalysisRequest(
        session_id=session_id,
        cache_hit_ratio=85.5,
        connection_utilization=65.0,
        seq_scan_percent=25.0,
        active_connections=65,
        max_connections=100
    )

    result = analyze_metrics(metrics_req)
    print(f"✓ 指标分析完成")
    print(f"  - 缓存命中率: {result.cache_hit_ratio}%")
    print(f"  - 连接利用率: {result.connection_utilization}%")
    print(f"  - 健康分数: {result.health_score}\n")


def test_report_generation(session_id: str):
    """测试报告生成端点."""
    print("=" * 80)
    print("测试5: RCA报告生成")
    print("=" * 80)

    report_req = RCAReportRequest(
        session_id=session_id,
        include_log_analysis=True,
        include_query_analysis=True,
        include_metrics_analysis=True
    )

    result = generate_report(report_req)
    print(f"✓ 报告生成完成")
    print(f"  - 报告ID: {result.id}")
    print(f"  - 标题: {result.title}")
    print(f"  - 发现问题: {len(result.root_causes) if result.root_causes else 0}\n")

    # 显示报告摘要
    if result.markdown_content:
        print("报告摘要（Markdown）:")
        print("─" * 80)
        # 只显示前500字符
        print(result.markdown_content[:500] + "...")
        print("─" * 80 + "\n")


def main():
    """运行所有测试."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Postgres RCA 系统集成测试" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝\n")

    try:
        # 测试1: 子代理注册
        if not test_subagents():
            return False

        # 测试2: 创建会话并分析日志
        session_id = test_log_analysis()

        # 测试3: 查询分析
        test_query_analysis(session_id)

        # 测试4: 性能指标分析
        test_metrics_analysis(session_id)

        # 测试5: 生成报告
        test_report_generation(session_id)

        # 总结
        print("=" * 80)
        print("✓ 所有测试通过！")
        print("=" * 80)
        print("\nRCA系统已准备就绪。使用方式：")
        print("  1. FastAPI: python -m app.main")
        print("  2. CLI模式: python -m app.main --cli")
        print("  3. 单次分析: python -m app.main --cli --input '你的问题'\n")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
