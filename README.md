# 信创组件适配评估系统

基于Flask的轻量级API框架，用于信创组件的适配性评估和性能分析。

## 功能特性

- **基于组件的适配评估**：根据现有组件推荐相关组件和依赖环境
- **基于任务的适配评估**：根据任务约束推荐满足条件的组件组合
- **性能评估**：提供组件组合的性能指标和资源需求
- **适配率指标**：计算各种适配率指标

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## API接口

### 1. 健康检查
```
GET /api/health
```

### 2. 获取组件列表
```
GET /api/components
GET /api/components/databases
GET /api/components/message-queues
GET /api/components/operating-systems
```

### 3. 基于组件的适配评估
```
POST /api/adaptation/component-based
Content-Type: application/json

{
  "target_database": "人大金仓 KingbaseES",
  "target_message_queue": "阿里 RabbitMQ",
  "target_operating_system": "麒麟 Kylin V10"
}
```

### 4. 基于任务的适配评估
```
POST /api/adaptation/task-based
Content-Type: application/json

{
  "task_type": "OLTP",
  "max_response_time": 1000,
  "min_throughput": 1000,
  "resource_constraints": {
    "max_cpu_cores": 8,
    "max_memory_gb": 16
  }
}
```

### 5. 性能评估
```
POST /api/performance/evaluate
Content-Type: application/json

{
  "database": "人大金仓 KingbaseES",
  "message_queue": "阿里 RabbitMQ",
  "operating_system": "麒麟 Kylin V10",
  "workload": "medium"
}
```

### 6. 适配率指标
```
GET /api/metrics/adaptation-rate
```

## 数据结构

### 组件数据 (data/components.json)
包含数据库、消息队列、操作系统的详细信息，包括版本、协议、兼容性标签和性能基线。

### 性能数据 (data/performance.json)
包含不同工作负载下的性能指标和组件组合的兼容性评分。

## 评估指标

1. **数据库×消息队列适配率**：反映组件层面兼容性判断的准确性
2. **组件适配依赖关系识别率**：衡量跨组件依赖关系的识别能力
3. **数据库×操作系统适配率**：评价跨操作系统的适配判定准确性

## 技术栈

- Python 3.7+
- Flask 2.3.3
- Flask-CORS 4.0.0
- JSON数据存储
