# Schema 组织文档

## 概述

所有 Pydantic BaseModel 类已集中管理在 `app/schemas/` 目录中，按功能分为 5 个专门的模块文件。

## 文件结构

```
app/schemas/
├── __init__.py          # 统一导出所有schema
├── session.py           # 会话相关模型 (2)
├── analysis.py          # 分析相关模型 (6)
├── report.py            # 报告相关模型 (2)
├── agent.py             # 多智能体API模型 (5)
└── common.py            # 通用模型 (3)
```

## 模块详细说明

### 1. `session.py` - 会话管理 (2 个模型)

处理 RCA 会话的创建和管理。

**模型列表**:
- `RCASessionCreate` - 创建会话请求
- `RCASessionResponse` - 会话响应

**使用位置**:
- `app/routers/__init__.py` - RCA 会话管理端点

### 2. `analysis.py` - 分析功能 (6 个模型)

处理各类数据分析（日志、查询、指标）的请求和响应。

**模型列表**:
- `LogAnalysisRequest` - 日志分析请求
- `LogAnalysisResponse` - 日志分析响应
- `QueryAnalysisRequest` - 查询分析请求
- `QueryAnalysisResponse` - 查询分析响应
- `MetricsAnalysisRequest` - 指标分析请求
- `MetricsAnalysisResponse` - 指标分析响应

**使用位置**:
- `app/routers/__init__.py` - RCA 分析端点

### 3. `report.py` - 报告生成 (2 个模型)

处理 RCA 报告的生成和管理。

**模型列表**:
- `RCAReportRequest` - 生成报告请求
- `RCAReportResponse` - 报告响应

**使用位置**:
- `app/routers/__init__.py` - 报告生成端点

### 4. `agent.py` - 多智能体 API (5 个模型)

处理多智能体系统的请求和响应。

**模型列表**:
- `AgentQueryRequest` - 代理查询请求
- `AgentQueryResponse` - 代理查询响应
- `AnalyzeRequest` - 综合分析请求
- `StreamMessage` - 流式消息
- `AgentHealthResponse` - 代理健康检查响应

**使用位置**:
- `app/api/agent.py` - 多智能体 API 端点

### 5. `common.py` - 通用模型 (3 个模型)

处理通用的响应和检查格式。

**模型列表**:
- `ErrorResponse` - 错误响应
- `SuccessResponse` - 成功响应
- `HealthCheckResponse` - 健康检查响应

**使用位置**:
- 全局使用，可被任何需要的模块导入

## 导入方式

### 统一导入（推荐）

```python
from app.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    AnalyzeRequest,
)
```

### 分类导入

```python
from app.schemas.agent import AgentQueryRequest
from app.schemas.analysis import LogAnalysisRequest
from app.schemas.session import RCASessionCreate
```

### 导出声明

每个模块都有 `__all__` 声明，清楚地表明该模块导出哪些类。

## 代码更新清单

### 已完成的更新

✓ **app/schemas/__init__.py**
  - 从各个子模块导入所有 BaseModel 类
  - 导出统一的 `__all__` 列表

✓ **app/schemas/session.py**
  - 创建 - 包含 RCASessionCreate 和 RCASessionResponse

✓ **app/schemas/analysis.py**
  - 创建 - 包含 6 个分析相关模型

✓ **app/schemas/report.py**
  - 创建 - 包含 RCAReportRequest 和 RCAReportResponse

✓ **app/schemas/agent.py**
  - 创建 - 包含 5 个多智能体相关模型

✓ **app/schemas/common.py**
  - 创建 - 包含 3 个通用模型

✓ **app/api/agent.py**
  - 移除所有 BaseModel 类定义
  - 更新导入：从 `app.schemas` 导入所需模型
  - 删除了 `from pydantic import BaseModel, Field` 的导入

✓ **app/routers/__init__.py**
  - 已使用新的 schema 导入路径（无需修改）

## 优势

1. **集中管理** - 所有数据模型在一个清晰的目录结构中
2. **易于维护** - 按功能分类，便于查找和修改
3. **减少循环导入** - API 模块不再包含模型定义
4. **便于重用** - 其他模块可以轻松导入需要的模型
5. **清晰的职责** - 模块划分清晰，职责单一

## 验证清单

✓ 所有 17 个模型都可成功导入
✓ FastAPI 应用正常加载（24 条路由）
✓ 所有 API 端点功能完整
✓ 类型提示和验证正常工作

## 最佳实践

### 添加新的 Schema

1. 确定所属类别
2. 在对应的 `.py` 文件中添加 BaseModel 类
3. 在模块的 `__all__` 中更新导出列表
4. 在 `__init__.py` 中添加导入

### 示例：添加新的会话模型

```python
# app/schemas/session.py 中添加
class RCASessionUpdate(BaseModel):
    """更新会话的请求."""
    description: Optional[str] = None
    status: Optional[str] = None

# __all__ 中添加
__all__ = [
    "RCASessionCreate",
    "RCASessionResponse",
    "RCASessionUpdate",  # 新增
]
```

```python
# app/schemas/__init__.py 中添加
from app.schemas.session import (
    RCASessionCreate,
    RCASessionResponse,
    RCASessionUpdate,  # 新增
)
```

## 文件大小统计

| 模块 | 行数 | 模型数 |
|------|------|--------|
| session.py | 34 | 2 |
| analysis.py | 103 | 6 |
| report.py | 33 | 2 |
| agent.py | 70 | 5 |
| common.py | 34 | 3 |
| __init__.py | 63 | - |
| **总计** | **337** | **17** |

## 后续改进建议

1. **添加 API 文档字符串** - 为每个模型字段添加详细描述
2. **添加验证器** - 使用 Pydantic 的 `@validator` 装饰器
3. **创建 schema 版本** - 支持 API 向后兼容性
4. **数据库模型关联** - 添加从 ORM 模型的转换方法

## 相关文档

- [API_GUIDE.md](API_GUIDE.md) - API 端点使用文档
- [CLAUDE.md](CLAUDE.md) - 项目开发指南
- [API_DEPLOYMENT.md](API_DEPLOYMENT.md) - 部署指南
