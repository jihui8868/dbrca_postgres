# 子代理系统

本目录包含多个专业化的子代理（SubAgent），每个子代理负责特定的任务域。主代理通过 `task` 工具委派任务给子代理。

## 架构设计

- **每个子代理一个文件**：便于维护和扩展
- **工具定义**：使用 `@tool` 装饰器定义工具函数
- **创建函数**：每个子代理都有一个 `create_xxx_agent()` 函数
- **统一导出**：所有子代理在 `__init__.py` 中聚合为 `ALL_SUBAGENTS` 列表

## 现有子代理

### 1. log_analyzer - Postgres 日志分析

**文件**: `log_analyzer.py`

**职责**: 解析和分析Postgres错误日志，识别问题模式，提供故障诊断建议

**工具列表**:

| 工具 | 功能 |
|------|------|
| `parse_postgres_log` | 解析日志文件，提取结构化信息 |
| `extract_errors` | 提取特定严重级别的错误信息 |
| `analyze_log_patterns` | 识别日志中的常见问题模式 |
| `summarize_issues` | 汇总问题和提供故障排查建议 |

**使用示例**:

主代理会自动调用此子代理来处理日志分析任务：

```
用户: 分析这些Postgres日志，找出问题
主代理: 我将委派给 log_analyzer 进行分析...
```

**支持的问题模式**:

- 连接问题（连接拒绝、超时）
- 认证和权限问题
- 内存和磁盘空间问题
- 死锁和锁争用
- 复制和WAL问题
- 慢查询问题

## 如何创建新的子代理

### 步骤 1: 创建新文件

在 `subagents/` 目录下创建新文件，例如 `data_parser.py`

### 步骤 2: 定义工具

```python
from langchain_core.tools import tool

@tool
def your_tool_name(input_param: str) -> dict:
    """工具描述"""
    # 实现工具逻辑
    return {}
```

### 步骤 3: 创建子代理

```python
from deepagents import SubAgent

def create_data_parser_agent() -> SubAgent:
    """创建数据解析子代理"""
    return SubAgent(
        name="data_parser",
        description="解析和提取数据",
        system_prompt="你是一个数据解析专家...",
        tools=[your_tool_name, another_tool]
    )

# 导出实例
data_parser_agent = create_data_parser_agent()
```

### 步骤 4: 注册到主代理

在 `__init__.py` 中添加：

```python
from app.agents.subagents.data_parser import data_parser_agent

ALL_SUBAGENTS = [
    log_analyzer_agent,
    data_parser_agent,  # 新增
    # ...
]
```

### 步骤 5: 更新主代理的系统提示

在 `app/agents/main_agent.py` 中更新 `MAIN_SYSTEM_PROMPT`，描述新子代理的功能。

## 工具定义最佳实践

### 使用 @tool 装饰器

```python
from langchain_core.tools import tool
from typing import Any

@tool
def process_data(content: str, threshold: int = 10) -> dict[str, Any]:
    """处理数据的工具描述.
    
    Args:
        content: 输入内容
        threshold: 阈值参数
        
    Returns:
        处理结果
    """
    # 实现逻辑
    return {"result": "..."}
```

### 当工具需要内部调用其他工具时

避免直接调用被 `@tool` 装饰的函数（会导致StructuredTool调用错误）。

解决方案：提取实现到私有函数

```python
def _tool_impl(param: str) -> dict:
    """工具的实现逻辑（私有）"""
    return {}

@tool
def my_tool(param: str) -> dict:
    """公开的工具接口"""
    return _tool_impl(param)

# 在其他工具中，直接调用私有函数
@tool
def composite_tool(param: str) -> dict:
    """使用其他工具的复合工具"""
    result1 = _tool_impl(param)
    # 继续处理
    return {}
```

## 子代理通信

子代理之间不直接通信，而是通过主代理：

```
用户 → 主代理 
       ↓
       └─→ task(log_analyzer) 
       ↓
       └─→ task(report_gen)
       ↓
       返回最终结果 → 用户
```

主代理负责：
- 理解用户意图
- 选择合适的子代理
- 传递中间结果
- 整合最终答案

## 测试子代理

### 单元测试

```bash
# 运行日志分析子代理的单位测试
python test_log_analyzer.py
```

### 集成测试

```bash
# 运行与主代理的集成测试
python test_integration.py
```

### CLI 模式测试

```bash
# 启动CLI模式，手动测试子代理
python -m app.main --cli --debug

# 在CLI中输入命令触发子代理调用
> 分析这些Postgres日志...
```

## 配置和扩展

### 修改系统提示

每个子代理的 `system_prompt` 定义了其行为。要调整子代理的行为，修改其系统提示：

```python
return SubAgent(
    name="log_analyzer",
    system_prompt="你是一个更加严格的日志分析专家...",
    ...
)
```

### 添加新工具

要为现有子代理添加新工具，只需在文件中定义新工具并添加到工具列表：

```python
def create_log_analyzer_agent() -> SubAgent:
    return SubAgent(
        ...
        tools=[
            parse_postgres_log,
            extract_errors,
            analyze_log_patterns,
            summarize_issues,
            new_tool,  # 添加新工具
        ]
    )
```

## 常见问题

### Q: 子代理可以直接调用其他子代理吗？

A: 不可以。子代理通过主代理的 `task` 工具进行协调。主代理会根据需要调用合适的子代理。

### Q: 如何传递复杂的数据结构给子代理？

A: 工具参数应该是简单的标量类型（字符串、数字）或JSON可序列化的结构。大数据应该保存为文件，通过文件路径传递。

### Q: 子代理的执行超时时间是多少？

A: 由主代理的 `max_iterations` 配置控制（默认50次迭代）。可在 `.env` 文件中配置：

```
AGENT__MAX_ITERATIONS=50
```
