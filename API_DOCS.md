# 信创组件适配评估系统 API 文档

## 概述

本系统提供基于组件和基于任务的信创组件适配评估API接口，支持数据库、消息队列、操作系统的兼容性分析和性能评估。

## 基础信息

- **基础URL**: `http://localhost:5000`
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

## 接口列表

### 1. 系统状态

#### 健康检查
```http
GET /api/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "message": "信创组件适配评估系统运行正常"
}
```

### 2. 组件管理

#### 获取所有组件
```http
GET /api/components
```

**响应示例**:
```json
{
  "databases": [...],
  "message_queues": [...],
  "operating_systems": [...]
}
```

#### 获取数据库组件
```http
GET /api/components/databases
```

#### 获取消息队列组件
```http
GET /api/components/message-queues
```

#### 获取操作系统组件
```http
GET /api/components/operating-systems
```

### 3. 适配评估

#### 基于组件的适配评估
```http
POST /api/adaptation/component-based
Content-Type: application/json
```

**请求参数**:
```json
{
  "target_database": "人大金仓 KingbaseES",
  "target_message_queue": "阿里 RabbitMQ",
  "target_operating_system": "麒麟 Kylin V10"
}
```

**响应示例**:
```json
{
  "compatibility_score": 0.92,
  "is_compatible": true,
  "recommendations": [
    {
      "type": "database",
      "recommended": [...],
      "reason": "基于协议兼容性推荐"
    }
  ],
  "dependencies": {
    "runtime_requirements": ["Java 8+", "Python 3.7+"],
    "driver_requirements": ["JDBC驱动", "AMQP客户端"],
    "protocol_stack": ["TCP/IP", "HTTP/HTTPS"],
    "os_requirements": ["Linux内核3.10+"]
  }
}
```

#### 基于任务的适配评估
```http
POST /api/adaptation/task-based
Content-Type: application/json
```

**请求参数**:
```json
{
  "task_type": "OLTP",
  "max_response_time": 1000,
  "min_throughput": 1000,
  "resource_constraints": {
    "max_cpu_cores": 8,
    "max_memory_gb": 16,
    "max_disk_gb": 500
  }
}
```

**响应示例**:
```json
{
  "task_type": "OLTP",
  "constraints": {
    "max_response_time": 1000,
    "min_throughput": 1000,
    "resource_constraints": {...}
  },
  "recommendations": [
    {
      "database": "人大金仓 KingbaseES",
      "message_queue": "阿里 RabbitMQ",
      "operating_system": "麒麟 Kylin V10",
      "estimated_performance": {
        "throughput": 1200,
        "response_time": 800
      },
      "resource_requirements": {
        "cpu_cores": 4,
        "memory_gb": 8,
        "disk_gb": 100
      }
    }
  ]
}
```

### 4. 性能评估

#### 性能评估
```http
POST /api/performance/evaluate
Content-Type: application/json
```

**请求参数**:
```json
{
  "database": "人大金仓 KingbaseES",
  "message_queue": "阿里 RabbitMQ",
  "operating_system": "麒麟 Kylin V10",
  "workload": "medium"
}
```

**响应示例**:
```json
{
  "components": {
    "database": "人大金仓 KingbaseES",
    "message_queue": "阿里 RabbitMQ",
    "operating_system": "麒麟 Kylin V10"
  },
  "workload": "medium",
  "performance_metrics": {
    "throughput": 1000,
    "latency_p50": 50,
    "latency_p95": 100,
    "cpu_usage": 60,
    "memory_usage": 70
  }
}
```

### 5. 评估指标

#### 获取适配率指标
```http
GET /api/metrics/adaptation-rate
```

**响应示例**:
```json
{
  "database_message_queue_rate": 0.85,
  "database_message_queue_dependency_rate": 0.80,
  "database_operating_system_rate": 0.90,
  "overall_accuracy": 0.85
}
```

## 错误处理

所有接口在出错时都会返回相应的HTTP状态码和错误信息：

```json
{
  "error": "错误描述信息"
}
```

常见状态码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 使用示例

### Python示例
```python
import requests

# 健康检查
response = requests.get("http://localhost:5000/api/health")
print(response.json())

# 基于组件的适配评估
data = {
    "target_database": "人大金仓 KingbaseES",
    "target_message_queue": "阿里 RabbitMQ",
    "target_operating_system": "麒麟 Kylin V10"
}
response = requests.post("http://localhost:5000/api/adaptation/component-based", json=data)
print(response.json())
```

### curl示例
```bash
# 健康检查
curl -X GET http://localhost:5000/api/health

# 基于任务的适配评估
curl -X POST http://localhost:5000/api/adaptation/task-based \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "OLTP",
    "max_response_time": 1000,
    "min_throughput": 1000
  }'
```
