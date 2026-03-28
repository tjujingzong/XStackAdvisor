"""
信创组件适配评估系统 - API测试脚本

测试列表：
1. 测试基于组件的适配评估（使用数据：datas/components.json）
2. 测试基于任务的适配评估（使用假数据：不依赖CSV文件）
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_component_based_adaptation():
    """测试基于组件的适配评估"""
    data = {
        "target_database": "人大金仓 KingbaseES",
        "target_message_queue": "阿里 RabbitMQ",
        "target_operating_system": "麒麟 Kylin V10"
    }
    response = requests.post(f"{BASE_URL}/api/adaptation/component-based", json=data)
    print("基于组件的适配评估:", json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_task_based_adaptation():
    """测试基于任务的适配评估"""
    data = {
        # 任务类型支持：OLTP / OLAP，这里使用 OLAP 进行测试
        "task_type": "OLAP",
        "max_response_time": 1000,
        "min_throughput": 1000,
        "resource_constraints": {
            "max_cpu_cores": 8,
            "max_memory_gb": 16
        }
    }
    response = requests.post(f"{BASE_URL}/api/adaptation/task-based", json=data)
    
    print("--- 响应头信息 ---")
    print(f"Request ID: {response.headers.get('X-Request-ID')}")
    print(f"Response Time: {response.headers.get('X-Response-Time')}")
    print("----------------")
    
    print("基于任务的适配评估推荐方案:", json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_reproduce_accuracy_easy_to_be_one():
    """复现：组件选择较少时 accuracy 容易为 1"""
    cases = [
        {
            "name": "仅操作系统(麒麟)",
            "payload": {
                "target_operating_system": "麒麟 Kylin V10",
            },
        },
        {
            "name": "仅操作系统(统信)",
            "payload": {
                "target_operating_system": "统信 UOS V20",
            },
        },
        {
            "name": "操作系统 + 数据库(人大金仓)",
            "payload": {
                "target_database": "人大金仓 KingbaseES",
                "target_operating_system": "麒麟 Kylin V10",
            },
        },
        {
            "name": "操作系统 + 数据库(达梦)",
            "payload": {
                "target_database": "达梦数据库",
                "target_operating_system": "统信 UOS V20",
            },
        },
        {
            "name": "操作系统 + 消息队列(RabbitMQ)",
            "payload": {
                "target_message_queue": "阿里 RabbitMQ",
                "target_operating_system": "麒麟 Kylin V10",
            },
        },
        {
            "name": "操作系统 + 消息队列(BES MQ)",
            "payload": {
                "target_message_queue": "宝兰德 BES MQ",
                "target_operating_system": "统信 UOS V20",
            },
        },
        {
            "name": "操作系统 + 中间件(TongLink)",
            "payload": {
                "target_middleware": "东方通 TongLink/Q",
                "target_operating_system": "麒麟 Kylin V10",
            },
        },
        {
            "name": "操作系统 + 中间件(Tengine)",
            "payload": {
                "target_middleware": "阿里 Tengine",
                "target_operating_system": "统信 UOS V20",
            },
        },
        {
            "name": "全选(数据库+MQ+OS)",
            "payload": {
                "target_database": "人大金仓 KingbaseES",
                "target_message_queue": "阿里 RabbitMQ",
                "target_operating_system": "麒麟 Kylin V10",
            },
        },
    ]

    for case in cases:
        resp = requests.post(f"{BASE_URL}/api/adaptation/component-based", json=case["payload"])
        body = resp.json()
        print(f"{case['name']} accuracy: {body.get('accuracy')}")


def test_reproduce_olap_accuracy_easy_to_be_one():
    """复现：OLAP 任务评估 accuracy 容易为 1"""
    cases = [
        {
            "name": "OLAP-默认约束",
            "payload": {
                "task_type": "OLAP",
                "max_response_time": 1000,
                "min_throughput": 1000,
                "resource_constraints": {
                    "max_cpu_cores": 8,
                    "max_memory_gb": 16,
                },
            },
        },
        {
            "name": "OLAP-宽松约束",
            "payload": {
                "task_type": "OLAP",
                "max_response_time": 1200,
                "min_throughput": 800,
                "resource_constraints": {
                    "max_cpu_cores": 12,
                    "max_memory_gb": 32,
                },
            },
        },
        {
            "name": "OLAP-较严格约束",
            "payload": {
                "task_type": "OLAP",
                "max_response_time": 900,
                "min_throughput": 1200,
                "resource_constraints": {
                    "max_cpu_cores": 8,
                    "max_memory_gb": 16,
                },
            },
        },
    ]

    for case in cases:
        resp = requests.post(f"{BASE_URL}/api/adaptation/task-based", json=case["payload"])
        body = resp.json()
        print(f"{case['name']} accuracy: {body.get('accuracy')}")


if __name__ == "__main__":
    try:
        test_reproduce_olap_accuracy_easy_to_be_one()
        print("=" * 50)
        print("复现测试完成")

    except requests.exceptions.ConnectionError:
        print("错误：无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"测试过程中出现错误：{e}")
