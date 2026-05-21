#!/usr/bin/env python3
"""FastAPI多智能体API集成测试."""

import asyncio
import json
import httpx
from typing import Optional

# API基URL
BASE_URL = "http://localhost:7777"


class RCATestClient:
    """RCA API测试客户端."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client()
        self.async_client = None

    async def __aenter__(self):
        self.async_client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.async_client:
            await self.async_client.aclose()

    def test_health_check(self) -> dict:
        """测试健康检查."""
        response = self.client.get(f"{self.base_url}/api/agent/health")
        return response.json()

    def test_query(self, query: str, session_id: Optional[str] = None) -> dict:
        """测试同步查询."""
        response = self.client.post(
            f"{self.base_url}/api/agent/query",
            json={"query": query, "session_id": session_id}
        )
        return response.json()

    def test_analyze(
        self,
        query: str,
        log_content: Optional[str] = None,
        explain_plan: Optional[str] = None,
        metrics: Optional[dict] = None
    ) -> dict:
        """测试综合分析."""
        data = {"query": query}
        if log_content:
            data["log_content"] = log_content
        if explain_plan:
            data["explain_plan"] = explain_plan
        if metrics:
            data["metrics"] = metrics

        response = self.client.post(
            f"{self.base_url}/api/agent/analyze",
            json=data
        )
        return response.json()

    def test_diagnose(self, db_host: str, issue_description: str) -> dict:
        """测试数据库诊断."""
        response = self.client.post(
            f"{self.base_url}/api/agent/diagnose",
            params={
                "db_host": db_host,
                "issue_description": issue_description
            }
        )
        return response.json()

    def test_list_sessions(self) -> dict:
        """测试列出会话."""
        response = self.client.get(f"{self.base_url}/api/agent/sessions")
        return response.json()

    def test_get_session(self, session_id: str) -> dict:
        """测试获取会话信息."""
        response = self.client.get(
            f"{self.base_url}/api/agent/sessions/{session_id}"
        )
        return response.json()


def print_header(title: str) -> None:
    """打印测试标题."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_test(name: str, result: bool, details: str = "") -> None:
    """打印测试结果."""
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"    {details}")


def main():
    """运行所有测试."""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "Postgres RCA - FastAPI 集成测试" + " "*26 + "║")
    print("╚" + "="*78 + "╝")

    client = RCATestClient()
    test_results = []

    # 测试1: 健康检查
    print_header("测试1: 系统健康检查")
    try:
        result = client.test_health_check()
        success = result.get("status") == "healthy"
        test_results.append(success)

        print_test(
            "健康检查",
            success,
            f"状态: {result.get('status')}, 代理数: {len(result.get('agent_status', {}))}"
        )
    except Exception as e:
        print_test("健康检查", False, str(e))
        test_results.append(False)

    # 测试2: 同步查询
    print_header("测试2: 同步查询")
    try:
        result = client.test_query("分析这个错误：connection refused")
        success = "session_id" in result and "response" in result
        test_results.append(success)

        session_id = result.get("session_id")
        processing_time = result.get("processing_time_ms", 0)

        print_test(
            "同步查询",
            success,
            f"会话: {session_id}, 耗时: {processing_time:.0f}ms"
        )

        # 保存会话ID用于后续测试
        test_session_id = session_id

    except Exception as e:
        print_test("同步查询", False, str(e))
        test_results.append(False)
        test_session_id = None

    # 测试3: 综合分析
    print_header("测试3: 综合分析")
    try:
        result = client.test_analyze(
            query="连接被拒绝",
            log_content="2024-05-21 ERROR: connection refused",
            metrics={"cache_hit_ratio": 85.5, "connection_utilization": 65.0}
        )
        success = "session_id" in result and "response" in result
        test_results.append(success)

        print_test(
            "综合分析",
            success,
            f"会话: {result.get('session_id')}, 耗时: {result.get('processing_time_ms', 0):.0f}ms"
        )
    except Exception as e:
        print_test("综合分析", False, str(e))
        test_results.append(False)

    # 测试4: 数据库诊断
    print_header("测试4: 数据库诊断")
    try:
        result = client.test_diagnose(
            db_host="localhost",
            issue_description="数据库连接经常被拒绝"
        )
        success = "session_id" in result and "diagnosis" in result
        test_results.append(success)

        print_test(
            "数据库诊断",
            success,
            f"会话: {result.get('session_id')}, 诊断长度: {len(result.get('diagnosis', ''))} 字符"
        )
    except Exception as e:
        print_test("数据库诊断", False, str(e))
        test_results.append(False)

    # 测试5: 列出会话
    print_header("测试5: 会话管理")
    try:
        result = client.test_list_sessions()
        success = "total_sessions" in result and "sessions" in result
        test_results.append(success)

        print_test(
            "列出会话",
            success,
            f"活跃会话数: {result.get('total_sessions', 0)}"
        )
    except Exception as e:
        print_test("列出会话", False, str(e))
        test_results.append(False)

    # 测试6: 获取会话信息
    if test_session_id:
        print_header("测试6: 获取会话信息")
        try:
            result = client.test_get_session(test_session_id)
            success = result.get("session_id") == test_session_id
            test_results.append(success)

            print_test(
                "获取会话信息",
                success,
                f"会话: {result.get('session_id')}, 查询次数: {result.get('query_count', 0)}"
            )
        except Exception as e:
            print_test("获取会话信息", False, str(e))
            test_results.append(False)

    # 总结
    print_header("测试总结")
    total_tests = len(test_results)
    passed_tests = sum(test_results)
    failed_tests = total_tests - passed_tests

    print(f"总测试数:  {total_tests}")
    print(f"通过:     {passed_tests} ✓")
    print(f"失败:     {failed_tests} ✗")
    print(f"成功率:   {passed_tests/total_tests*100:.1f}%")

    if failed_tests == 0:
        print("\n" + "="*80)
        print("✓ 所有测试通过！FastAPI多智能体系统已准备就绪")
        print("="*80 + "\n")
        return True
    else:
        print("\n" + "="*80)
        print(f"✗ {failed_tests} 个测试失败，请检查服务器状态")
        print("="*80 + "\n")
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        print("\n检查事项:")
        print("1. FastAPI服务器是否正在运行: python -m app.main")
        print("2. 检查配置文件 .env 是否正确设置")
        print("3. 查看服务器日志获取更多信息")
        exit(1)
