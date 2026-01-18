"""
信创组件适配评估系统 - API测试脚本

测试列表：
1. 测试健康检查接口
2. 测试组件列表接口
3. 测试基于组件的适配评估（使用数据：datas/components.json）
4. 测试基于任务的适配评估（使用真实数据：datas目录下的CSV文件）
5. 测试性能评估接口（使用真实数据：datas目录下的CSV文件）
6. 测试容量外推接口（使用真实数据：datas目录下的CSV文件）
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    """测试健康检查接口"""
    response = requests.get(f"{BASE_URL}/api/health")
    print("健康检查:", response.json())

def test_components():
    """测试组件列表接口"""
    response = requests.get(f"{BASE_URL}/api/components")
    print("组件列表:", json.dumps(response.json(), indent=2, ensure_ascii=False))

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
        "task_type": "OLTP",
        "max_response_time": 1000,
        "min_throughput": 1000,
        "resource_constraints": {
            "max_cpu_cores": 8,
            "max_memory_gb": 16
        }
    }
    response = requests.post(f"{BASE_URL}/api/adaptation/task-based", json=data)
    print("基于任务的适配评估:", json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_performance_evaluation():
    """测试性能评估接口（基于CSV真实数据）"""
    data = {
        "database": "人大金仓 KingbaseES",
        "message_queue": "阿里 RabbitMQ",
        "operating_system": "麒麟 Kylin V10"
    }
    response = requests.post(f"{BASE_URL}/api/performance/evaluate", json=data)
    print("性能评估:", json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_capacity_extrapolation():
    """测试容量外推接口：根据组件名称和目标性能计算所需CPU和内存"""
    # 测试数据库容量外推
    data_db = {
        "component_name": "KingbaseES",
        "component_type": "DB",
        "target_tps": 1000,
        "max_latency_ms": 100,
        "test_cpu_cores": 4,
        "test_memory_gb": 4.0
    }
    response = requests.post(f"{BASE_URL}/api/capacity/extrapolation", json=data_db)
    print("数据库容量外推:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 测试消息队列容量外推
    data_mq = {
        "component_name": "RabbitMQ",
        "component_type": "MQ",
        "target_msg_per_sec": 10000,
        "max_latency_ms": 100,
        "test_cpu_cores": 4,
        "test_memory_gb": 4.0
    }
    response = requests.post(f"{BASE_URL}/api/capacity/extrapolation", json=data_mq)
    print("\n消息队列容量外推:", json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("开始测试信创组件适配评估系统API...")
    print("=" * 50)
    
    try:
        test_health()
        print("\n" + "=" * 50)
        
        test_components()
        print("\n" + "=" * 50)
        
        test_component_based_adaptation()
        print("\n" + "=" * 50)
        
        test_task_based_adaptation()
        print("\n" + "=" * 50)
        
        test_performance_evaluation()
        print("\n" + "=" * 50)
        
        test_capacity_extrapolation()
        print("\n" + "=" * 50)
        
        print("所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"测试过程中出现错误：{e}")
