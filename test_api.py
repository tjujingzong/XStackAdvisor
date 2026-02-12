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
        # 任务类型支持：OLTP / ALTP，这里使用 ALTP 进行测试
        "task_type": "ALTP",
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


if __name__ == "__main__":
    print("开始测试信创组件适配评估系统API...")
    print("=" * 50)
    
    try:
        test_component_based_adaptation()
        print("\n" + "=" * 50)
        
        test_task_based_adaptation()
        print("\n" + "=" * 50)
        
        print("所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"测试过程中出现错误：{e}")
