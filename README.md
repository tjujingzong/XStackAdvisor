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

### 5. 性能评估（基于CSV真实数据）
```
POST /api/performance/evaluate
Content-Type: application/json

{
  "database": "人大金仓 KingbaseES",
  "message_queue": "阿里 RabbitMQ",
  "operating_system": "麒麟 Kylin V10"
}
```

返回从CSV文件中提取的真实性能数据，包括吞吐量、延迟、CPU和内存使用率等。

### 6. 获取真实环境性能数据
```
GET /api/performance/real-data/database
GET /api/performance/real-data/message-queue
GET /api/performance/real-data/database?component=KingbaseES
GET /api/performance/real-data/message-queue?component=RabbitMQ
```

返回真实环境采集的CSV数据（JSON格式）。支持可选参数：
- `component`: 组件名称过滤（如 "KingbaseES", "RabbitMQ"）
- `limit`: 返回记录数限制（默认：100）

### 6. 适配率指标
```
GET /api/metrics/adaptation-rate
```

## 数据结构

### 组件配置数据 (datas/components.json)
**组件元数据文件，包含版本、协议等配置信息，不包含性能数据。**

- **`datas/components.json`**：包含数据库、消息队列、操作系统的详细信息，包括：
  - `id`: 组件ID
  - `name`: 组件名称
  - `version`: 版本号
  - `vendor`: 厂商
  - `protocol`: 协议类型
  - `compatibility_tags`: 兼容性标签
  - **注意**：性能数据（如 TPS、延迟等）不再存储在此文件中，而是从真实环境测试的 CSV 文件中获取

### 真实环境数据 (datas/)
**`datas/` 目录包含从真实环境上采集的性能测试数据。**

- **组件配置**：`datas/components.json` - 组件元数据（版本、协议等信息）
- **数据库测试结果**：格式为 `{Component}_kbbench_results_{timestamp}.csv`
  - 包含字段：`timestamp`, `clients`, `jobs`, `duration_s`, `tps_including`, `tps_excluding`, `latency_ms_avg`, `tx_processed`, `return_code`, `error`, `avg_cpu_percent`, `max_cpu_percent`, `avg_memory_percent`, `max_memory_percent`, `avg_memory_used_gb`
  - **注意**：不是所有字段都是必需的，某些字段可能为空
  
- **消息队列测试结果**：
  - **汇总数据**：格式为 `{Component}_perftest_summary_{timestamp}.csv`
    - 包含字段：`run_id`, `target_rate_msg_s`, `avg_sent_msg_s`, `avg_received_msg_s`, `worst_p95_ms`, `success`, `note`, `duration_s`, `producers`, `consumers`, `size_bytes`, `queue`, `avg_cpu_percent`, `max_cpu_percent`, `avg_memory_percent`, `max_memory_percent`, `avg_memory_used_gb`
  - **时间序列数据**：格式为 `{Component}_perftest_timeseries_{timestamp}.csv`
  - **注意**：不是所有字段都是必需的，某些字段可能为空

## 数据生成工具

系统提供了两个工具用于处理真实环境采集的数据并生成归一化指标：

### 1. normalize_metrics.py - 归一化指标计算器

将小机测试结果转换为可外推的单位指标，计算以下指标：
- **单位核心吞吐**：TPS/核心数、msg/s/核心数
- **单位内存足迹**：内存占用/消息数、内存占用/事务数
- **单位消息/事务开销**：延迟/消息大小、吞吐/资源占用等

**使用方法：**
```bash
# 处理数据库测试结果
python normalize_metrics.py --db-csv datas/KingbaseES_kbbench_results_20251220_192650.csv --cpu-cores 4 --memory-gb 4.0

# 处理消息队列测试结果
python normalize_metrics.py --mq-summary-csv datas/RabbitMQ_perftest_summary_20251220_180415.csv --cpu-cores 4 --memory-gb 4.0

# 同时处理数据库和消息队列
python normalize_metrics.py \
  --db-csv datas/KingbaseES_kbbench_results_20251220_192650.csv \
  --mq-summary-csv datas/RabbitMQ_perftest_summary_20251220_180415.csv \
  --cpu-cores 4 \
  --memory-gb 4.0 \
  --output-dir datas
```

**主要参数：**
- `--db-csv`: 数据库测试结果CSV文件路径
- `--mq-summary-csv`: 消息队列测试汇总CSV文件路径
- `--output-dir`: 输出目录（默认：datas）
- `--cpu-cores`: 测试环境CPU核心数（默认：4）
- `--memory-gb`: 测试环境内存大小GB（默认：4.0）
- `--component-name-db`: 数据库组件名称（默认：KingbaseES）
- `--component-name-mq`: 消息队列组件名称（默认：RabbitMQ）

### 2. collect_and_normalize.py - 批量数据处理工具

自动扫描测试结果目录，批量处理并生成归一化指标。支持自动查找最新的测试结果文件。

**使用方法：**
```bash
# 批量处理 datas 目录下的所有测试结果
python collect_and_normalize.py --data-dir datas --cpu-cores 4 --memory-gb 4.0

# 执行容量外推示例（基于归一化数据）
python collect_and_normalize.py \
  --data-dir datas \
  --cpu-cores 4 \
  --memory-gb 4.0 \
  --extrapolate \
  --target-tps 10000 \
  --max-latency-ms 50
```

**主要参数：**
- `--data-dir`: 测试结果数据目录（默认：datas）
- `--cpu-cores`: 测试环境CPU核心数（默认：4）
- `--memory-gb`: 测试环境内存大小GB（默认：4.0）
- `--extrapolate`: 执行容量外推示例
- `--target-tps`: 目标TPS（用于容量外推）
- `--target-msg-per-sec`: 目标消息/秒（用于容量外推）
- `--max-latency-ms`: 最大延迟ms（用于容量外推，默认：50）

**文件查找规则：**
- 数据库：优先查找 `results.csv`，否则查找 `*_kbbench_results_*.csv` 或 `*kbbench*.csv`
- 消息队列：查找 `*perftest_summary_*.csv`

**输出：**
- 归一化指标统计摘要（控制台输出）
- 容量外推建议（如果启用 `--extrapolate`）

## 测试

### 运行测试代码

系统提供了 `test_api.py` 测试脚本，用于测试所有 API 接口的功能。

**使用方法：**

1. **确保服务已启动**
   ```bash
   python app.py
   ```

2. **在另一个终端运行测试**
   ```bash
   python test_api.py
   ```

**测试内容：**

测试脚本会依次测试以下接口：
- ✅ 健康检查接口 (`/api/health`)
- ✅ 组件列表接口 (`/api/components`)
- ✅ 基于组件的适配评估 (`/api/adaptation/component-based`)
- ✅ 基于任务的适配评估 (`/api/adaptation/task-based`)
- ✅ 性能评估接口 (`/api/performance/evaluate`)
- ✅ 适配率指标接口 (`/api/metrics/adaptation-rate`)
- ✅ 真实环境数据库数据接口 (`/api/performance/real-data/database`)
- ✅ 真实环境消息队列数据接口 (`/api/performance/real-data/message-queue`)

**测试示例输出：**
```
开始测试信创组件适配评估系统API...
==================================================
健康检查: {'status': 'healthy', 'message': '信创组件适配评估系统运行正常'}
==================================================
组件列表: {
  "databases": [...],
  "message_queues": [...],
  "operating_systems": [...]
}
...
```

**注意事项：**
- 测试前请确保 Flask 服务正在运行（`python app.py`）
- 如果服务运行在不同的端口，需要修改 `test_api.py` 中的 `BASE_URL`
- 测试真实环境数据接口时，需要确保 `datas/` 目录下有相应的 CSV 文件

## 评估指标

1. **数据库×消息队列适配率**：反映组件层面兼容性判断的准确性
2. **组件适配依赖关系识别率**：衡量跨组件依赖关系的识别能力
3. **数据库×操作系统适配率**：评价跨操作系统的适配判定准确性

## 常用命令

### 启动服务
```bash
# 开发模式启动
python app.py


```

### 运行测试
```bash
# 运行 API 测试（需要先启动服务）
python test_api.py
```

### 数据处理
```bash
# 批量处理测试数据并生成归一化指标
python collect_and_normalize.py --data-dir datas --cpu-cores 4 --memory-gb 4.0

# 处理单个数据库测试文件
python normalize_metrics.py --db-csv datas/KingbaseES_kbbench_results_20251220_192650.csv --cpu-cores 4 --memory-gb 4.0

# 处理单个消息队列测试文件
python normalize_metrics.py --mq-summary-csv datas/RabbitMQ_perftest_summary_20251220_180415.csv --cpu-cores 4 --memory-gb 4.0
```

### 下载数据
```bash
# 从 GitHub 下载测试数据到 datas 目录
python download_datas.py
```

## 技术栈

- Python 3.7+
- Flask 2.3.3
- Flask-CORS 4.0.0
- pandas 2.0.3（用于 CSV 数据处理）
- numpy 1.24.3（用于数值计算）
- JSON数据存储
