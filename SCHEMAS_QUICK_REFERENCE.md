# Schemas 快速参考

## 导入方式

### 方式 1: 统一导入（推荐）
```python
from app.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    LogAnalysisRequest,
    # ... 其他需要的模型
)
```

### 方式 2: 分类导入
```python
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.schemas.analysis import LogAnalysisRequest
from app.schemas.session import RCASessionCreate
```

## 所有可用的 Schemas

### Session 会话相关 (session.py)
```
RCASessionCreate        - 创建会话请求
RCASessionResponse      - 会话响应
```

### Analysis 分析相关 (analysis.py)
```
LogAnalysisRequest      - 日志分析请求
LogAnalysisResponse     - 日志分析响应
QueryAnalysisRequest    - 查询分析请求
QueryAnalysisResponse   - 查询分析响应
MetricsAnalysisRequest  - 指标分析请求
MetricsAnalysisResponse - 指标分析响应
```

### Report 报告相关 (report.py)
```
RCAReportRequest        - 生成报告请求
RCAReportResponse       - 报告响应
```

### Agent 多智能体相关 (agent.py)
```
AgentQueryRequest       - 代理查询请求
AgentQueryResponse      - 代理查询响应
AnalyzeRequest          - 综合分析请求
StreamMessage           - 流式消息
AgentHealthResponse     - 代理健康检查响应
```

### Common 通用 (common.py)
```
ErrorResponse           - 错误响应
SuccessResponse         - 成功响应
HealthCheckResponse     - 健康检查响应
```

## 常见使用场景

### 创建 FastAPI 端点

```python
from fastapi import APIRouter
from app.schemas import AgentQueryRequest, AgentQueryResponse

router = APIRouter()

@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(req: AgentQueryRequest) -> AgentQueryResponse:
    # 处理请求
    return AgentQueryResponse(
        session_id="...",
        query=req.query,
        response="...",
        timestamp=datetime.utcnow(),
        processing_time_ms=100.0
    )
```

### 在业务逻辑中使用

```python
from app.schemas import LogAnalysisRequest, LogAnalysisResponse

def analyze_logs(req: LogAnalysisRequest) -> LogAnalysisResponse:
    # 处理日志分析
    return LogAnalysisResponse(
        id="...",
        session_id=req.session_id,
        created_at=datetime.utcnow(),
        total_entries=100,
        error_count=5,
        warning_count=10,
        issues_found=3,
        analysis_result={...}
    )
```

### 在响应中使用

```python
from fastapi import HTTPException, status
from app.schemas import ErrorResponse

raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid request"
)
# 返回类似 ErrorResponse 的结构
```

## Schema 字段参考

### 时间字段
- 类型: `datetime`
- 创建方式: `datetime.utcnow()`

### ID 字段
- 类型: `str`
- 生成方式: `uuid.uuid4().hex[:16]`

### 可选字段
- 类型: `Optional[str]` 或 `Optional[dict[str, Any]]`
- 默认值: `None`

## 验证示例

```python
from app.schemas import AgentQueryRequest

# 有效请求
try:
    req = AgentQueryRequest(
        query="分析日志",
        session_id="abc123",
        debug=False
    )
    print("✓ 请求有效")
except Exception as e:
    print(f"✗ 验证失败: {e}")

# 无效请求（查询为空）
try:
    req = AgentQueryRequest(query="")
except Exception as e:
    print(f"✗ 验证失败: {e}")
    # validation error: value_error: at least 1 character
```

## 常见验证规则

### 查询/文本字段
- `min_length=1` - 必须至少 1 个字符
- `max_length=5000` - 最多 5000 个字符

### 数值字段
- `ge=0, le=100` - 范围在 0-100 之间
- `ge=1, le=65535` - 范围在 1-65535 之间

### 会话 ID
- `Optional[str]` - 可选，如果未提供则自动生成

## 添加新 Schema 的步骤

### 1. 选择合适的文件
```
类型 → 文件
会话相关 → session.py
分析相关 → analysis.py
报告相关 → report.py
多智能体 → agent.py
通用 → common.py
```

### 2. 创建模型
```python
# 在对应的 .py 文件中
class MyNewModel(BaseModel):
    """模型说明."""
    field1: str = Field(..., min_length=1)
    field2: Optional[int] = None
```

### 3. 更新 __all__
```python
__all__ = [
    "ExistingModel",
    "MyNewModel",  # 新增
]
```

### 4. 更新 __init__.py
```python
from app.schemas.yourmodule import MyNewModel
# 在 __all__ 中添加
__all__ = [
    # ...
    "MyNewModel",  # 新增
]
```

## 调试技巧

### 查看所有可用 Schemas
```python
import app.schemas
print(dir(app.schemas))
```

### 查看 Schema 的字段定义
```python
from app.schemas import AgentQueryRequest

print(AgentQueryRequest.model_json_schema())
```

### 测试 Schema 验证
```python
from app.schemas import AgentQueryRequest

# 创建实例
instance = AgentQueryRequest(query="test")

# 转换为 JSON
json_str = instance.model_dump_json()

# 转换为字典
data_dict = instance.model_dump()
```

## 性能建议

1. **避免在循环中创建模型实例** - 重用已创建的实例
2. **使用 dict 而非模型** - 对于大量数据处理，考虑先用 dict 处理再转换
3. **异步处理大型响应** - 使用 `AsyncGenerator` 处理流式数据

## 相关文件

- [SCHEMA_ORGANIZATION.md](SCHEMA_ORGANIZATION.md) - 详细的组织文档
- [app/schemas/](app/schemas/) - Schema 源代码
- [API_GUIDE.md](API_GUIDE.md) - API 端点使用指南
