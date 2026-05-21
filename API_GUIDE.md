# Postgres RCA - API 使用指南

本指南介绍如何调用多智能体分析API。

## 目录

1. [同步API](#同步api)
2. [流式API](#流式api)
3. [WebSocket API](#websocket-api)
4. [示例代码](#示例代码)

---

## 同步 API

### 1. 代理查询（Query Agent）

同步调用代理进行分析，返回完整结果。

**端点**: `POST /api/agent/query`

**请求体**:
```json
{
  "query": "分析这个Postgres日志：2024-05-21 ERROR: connection refused",
  "session_id": "optional-session-id",
  "debug": false
}
```

**响应**:
```json
{
  "session_id": "abc123",
  "query": "分析这个Postgres日志...",
  "response": "根据日志分析...",
  "timestamp": "2024-05-21T10:23:45.123456",
  "processing_time_ms": 2500.5
}
```

**使用示例**:
```bash
curl -X POST http://localhost:7777/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "分析这个错误：connection refused"
  }'
```

---

### 2. 问题分析（Analyze Issue）

综合日志、查询计划和性能指标进行分析。

**端点**: `POST /api/agent/analyze`

**查询参数**:
- `query` (required): 问题描述
- `log_content` (optional): 日志内容
- `explain_plan` (optional): SQL执行计划
- `metrics` (optional): 性能指标JSON

**响应**: 同查询API

**使用示例**:
```bash
curl -X POST http://localhost:7777/api/agent/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "数据库连接经常被拒绝",
    "log_content": "2024-05-21 ERROR: connection refused",
    "metrics": {
      "cache_hit_ratio": 85.5,
      "connection_utilization": 65.0
    }
  }'
```

---

### 3. 数据库诊断（Diagnose Database）

对数据库问题进行完整的诊断分析。

**端点**: `POST /api/agent/diagnose`

**查询参数**:
- `db_host` (required): 数据库主机
- `issue_description` (required): 问题描述

**响应**:
```json
{
  "session_id": "abc123",
  "db_host": "localhost",
  "issue": "连接频繁断开",
  "diagnosis": "诊断报告...",
  "processing_time_ms": 5000,
  "timestamp": "2024-05-21T10:23:45.123456"
}
```

**使用示例**:
```bash
curl -X POST "http://localhost:7777/api/agent/diagnose?db_host=localhost&issue_description=连接经常被拒绝"
```

---

## 流式 API

### 流式查询（Streaming Query）

以Server-Sent Events格式流式返回分析过程。

**端点**: `GET /api/agent/stream/{session_id}`

**查询参数**:
- `query` (required): 查询内容

**响应流**: 流式消息
```
data: {"type":"start","content":"开始分析...","timestamp":"2024-05-21T10:23:45"}
data: {"type":"thinking","content":"分析日志...","timestamp":"2024-05-21T10:23:46"}
data: {"type":"response","content":"根据分析...","timestamp":"2024-05-21T10:23:47"}
data: {"type":"end","content":"分析完成","timestamp":"2024-05-21T10:23:48"}
```

**使用示例（JavaScript）**:
```javascript
const eventSource = new EventSource(
  '/api/agent/stream/abc123?query=分析错误'
);

eventSource.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`[${message.type}] ${message.content}`);

  if (message.type === 'end') {
    eventSource.close();
  }
};

eventSource.onerror = (error) => {
  console.error('流式查询错误:', error);
  eventSource.close();
};
```

---

## WebSocket API

### 1. 实时分析（Analyze）

通过WebSocket进行实时问题分析。

**端点**: `WS /ws/analyze/{session_id}`

**发送消息**:
```json
{
  "query": "分析这个问题",
  "debug": false
}
```

**接收消息类型**:
- `start`: 分析开始
- `thinking`: 分析过程
- `response`: 最终响应
- `end`: 分析完成
- `error`: 错误信息

**使用示例（JavaScript）**:
```javascript
const ws = new WebSocket('ws://localhost:7777/ws/analyze/session123');

ws.onopen = () => {
  console.log('WebSocket连接已建立');
  ws.send(JSON.stringify({
    query: '分析这个错误：connection refused',
    debug: false
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'start':
      console.log('✓ 开始分析');
      break;
    case 'thinking':
      console.log('→ ' + message.content.substring(0, 100));
      break;
    case 'response':
      console.log('✓ 分析完成:\n' + message.content);
      break;
    case 'end':
      console.log(`✓ ${message.content}`);
      ws.close();
      break;
    case 'error':
      console.error('✗ 错误: ' + message.content);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket连接已关闭');
};
```

---

### 2. 多轮聊天（Chat）

通过WebSocket进行多轮对话，保持会话状态。

**端点**: `WS /ws/chat/{session_id}`

**发送消息**:
```json
{
  "query": "第一个问题"
}
```

**接收消息**:
```json
{
  "type": "response",
  "content": "答案...",
  "processing_time_ms": 1500,
  "message_count": 2,
  "timestamp": "2024-05-21T10:23:45.123456"
}
```

**使用示例（Python）**:
```python
import websocket
import json
import time

def on_message(ws, message):
    data = json.loads(message)
    print(f"[{data['type']}] {data.get('content', '')} "
          f"({data.get('processing_time_ms', 0):.0f}ms)")

def on_error(ws, error):
    print(f"错误: {error}")

def on_close(ws, close_status_code, close_msg):
    print("连接已关闭")

def on_open(ws):
    print("连接已建立")
    
    # 发送第一条消息
    ws.send(json.dumps({"query": "什么是Postgres缓存命中率？"}))

ws = websocket.WebSocketApp(
    "ws://localhost:7777/ws/chat/session123",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()

# 等待连接建立后，发送更多问题
time.sleep(2)
ws.send(json.dumps({"query": "如何提高缓存命中率？"}))
```

---

## 会话管理

### 列出所有会话

**端点**: `GET /api/agent/sessions`

**响应**:
```json
{
  "total_sessions": 3,
  "sessions": [
    {
      "session_id": "abc123",
      "created_at": "2024-05-21T10:23:45",
      "query_count": 5,
      "last_updated": "2024-05-21T10:25:30"
    }
  ]
}
```

---

### 获取会话信息

**端点**: `GET /api/agent/sessions/{session_id}`

**响应**:
```json
{
  "session_id": "abc123",
  "created_at": "2024-05-21T10:23:45",
  "query_count": 5,
  "last_query": "分析这个错误",
  "last_response": "根据分析..."
}
```

---

### 删除会话

**端点**: `DELETE /api/agent/sessions/{session_id}`

**响应**:
```json
{
  "message": "会话 abc123 已删除"
}
```

---

## 健康检查

**端点**: `GET /api/agent/health`

**响应**:
```json
{
  "status": "healthy",
  "session_count": 3,
  "agent_status": {
    "log_analyzer": "ready",
    "query_analyzer": "ready",
    "metrics_analyzer": "ready",
    "report_gen": "ready"
  },
  "timestamp": "2024-05-21T10:23:45"
}
```

---

## 示例代码

### Python 客户端

```python
import requests
import json

# API基URL
BASE_URL = "http://localhost:7777"

class RCAClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def query(self, query, session_id=None):
        """同步查询"""
        response = requests.post(
            f"{self.base_url}/api/agent/query",
            json={
                "query": query,
                "session_id": session_id
            }
        )
        return response.json()
    
    def analyze(self, query, log_content=None, explain_plan=None, metrics=None):
        """综合分析"""
        response = requests.post(
            f"{self.base_url}/api/agent/analyze",
            json={
                "query": query,
                "log_content": log_content,
                "explain_plan": explain_plan,
                "metrics": metrics
            }
        )
        return response.json()
    
    def diagnose(self, db_host, issue_description):
        """数据库诊断"""
        response = requests.post(
            f"{self.base_url}/api/agent/diagnose",
            params={
                "db_host": db_host,
                "issue_description": issue_description
            }
        )
        return response.json()
    
    def get_sessions(self):
        """获取所有会话"""
        response = requests.get(f"{self.base_url}/api/agent/sessions")
        return response.json()

# 使用示例
client = RCAClient()

# 查询
result = client.query("分析这个错误：connection refused")
print(f"会话: {result['session_id']}")
print(f"响应: {result['response']}")
print(f"耗时: {result['processing_time_ms']:.0f}ms")

# 综合分析
result = client.analyze(
    "连接被拒绝",
    log_content="2024-05-21 ERROR: connection refused",
    metrics={"connection_utilization": 85}
)

# 数据库诊断
result = client.diagnose(
    "localhost",
    "数据库连接经常被拒绝"
)
```

### JavaScript 客户端

```javascript
class RCAClient {
  constructor(baseUrl = 'http://localhost:7777') {
    this.baseUrl = baseUrl;
  }

  async query(query, sessionId = null) {
    const response = await fetch(`${this.baseUrl}/api/agent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId })
    });
    return response.json();
  }

  async analyze(query, logContent = null, explainPlan = null, metrics = null) {
    const response = await fetch(`${this.baseUrl}/api/agent/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        log_content: logContent,
        explain_plan: explainPlan,
        metrics
      })
    });
    return response.json();
  }

  async diagnose(dbHost, issueDescription) {
    const response = await fetch(
      `${this.baseUrl}/api/agent/diagnose?` +
      `db_host=${encodeURIComponent(dbHost)}&` +
      `issue_description=${encodeURIComponent(issueDescription)}`,
      { method: 'POST' }
    );
    return response.json();
  }

  streamAnalyze(sessionId, query) {
    return new EventSource(
      `${this.baseUrl}/api/agent/stream/${sessionId}?` +
      `query=${encodeURIComponent(query)}`
    );
  }

  wsAnalyze(sessionId) {
    return new WebSocket(
      `ws://localhost:7777/ws/analyze/${sessionId}`
    );
  }

  wsChat(sessionId) {
    return new WebSocket(
      `ws://localhost:7777/ws/chat/${sessionId}`
    );
  }
}

// 使用示例
const client = new RCAClient();

// 同步查询
client.query('分析这个错误：connection refused').then(result => {
  console.log(`会话: ${result.session_id}`);
  console.log(`响应: ${result.response}`);
});

// WebSocket实时分析
const ws = client.wsAnalyze('session123');
ws.onopen = () => {
  ws.send(JSON.stringify({
    query: '分析这个错误',
    debug: false
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`[${message.type}] ${message.content}`);
};
```

---

## 错误处理

### HTTP状态码

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器错误

### 错误响应示例

```json
{
  "detail": "会话 abc123 不存在"
}
```

---

## 最佳实践

1. **会话管理**
   - 重复使用会话ID保持对话上下文
   - 定期清理不使用的会话

2. **错误处理**
   - 实现重试机制
   - 记录错误日志

3. **性能优化**
   - 对于长时间运行的分析使用流式API
   - 使用WebSocket保持持久连接

4. **安全性**
   - 验证用户输入
   - 实施速率限制
   - 使用HTTPS/WSS

---

## 常见问题

**Q: 同步API和流式API有什么区别？**

A: 同步API等待完整分析结果后返回，流式API实时返回分析过程。选择同步API用于简单查询，流式API用于长时间运行的分析。

**Q: WebSocket连接支持多久？**

A: 连接将持续到显式关闭或网络中断。服务器会定期清理不活跃的会话。

**Q: 如何处理大量的日志或查询？**

A: 使用流式API或WebSocket，并考虑分批处理。

---

更多信息请查看 [CLAUDE.md](CLAUDE.md) 和 [子代理开发文档](app/agents/subagents/README.md)。
