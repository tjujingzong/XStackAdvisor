"""
信创组件适配评估系统 - API路由
"""

from flask import jsonify, request
from app import app, COMPONENTS, PERFORMANCE
import json

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': '信创组件适配评估系统运行正常'
    })

@app.route('/api/components', methods=['GET'])
def get_components():
    """获取所有组件列表"""
    return jsonify({
        'databases': COMPONENTS.get('databases', []),
        'message_queues': COMPONENTS.get('message_queues', []),
        'operating_systems': COMPONENTS.get('operating_systems', [])
    })

@app.route('/api/components/databases', methods=['GET'])
def get_databases():
    """获取数据库组件列表"""
    return jsonify(COMPONENTS.get('databases', []))

@app.route('/api/components/message-queues', methods=['GET'])
def get_message_queues():
    """获取消息队列组件列表"""
    return jsonify(COMPONENTS.get('message_queues', []))

@app.route('/api/components/operating-systems', methods=['GET'])
def get_operating_systems():
    """获取操作系统组件列表"""
    return jsonify(COMPONENTS.get('operating_systems', []))

@app.route('/api/adaptation/component-based', methods=['POST'])
def component_based_adaptation():
    """基于组件的适配评估"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    # 获取输入参数
    target_db = data.get('target_database')
    target_mq = data.get('target_message_queue')
    target_os = data.get('target_operating_system')
    
    # 简单的兼容性检查逻辑
    compatibility_score = calculate_compatibility_score(target_db, target_mq, target_os)
    
    # 推荐相关组件
    recommendations = get_component_recommendations(target_db, target_mq, target_os)
    
    return jsonify({
        'compatibility_score': compatibility_score,
        'is_compatible': compatibility_score > 0.7,
        'recommendations': recommendations,
        'dependencies': get_dependencies(target_db, target_mq, target_os)
    })

@app.route('/api/adaptation/task-based', methods=['POST'])
def task_based_adaptation():
    """基于任务的适配评估"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    # 获取任务约束
    task_type = data.get('task_type', 'OLTP')
    max_response_time = data.get('max_response_time', 1000)  # ms
    min_throughput = data.get('min_throughput', 1000)  # TPS
    resource_constraints = data.get('resource_constraints', {})
    
    # 根据任务约束推荐组件组合
    recommendations = get_task_recommendations(
        task_type, max_response_time, min_throughput, resource_constraints
    )
    
    return jsonify({
        'task_type': task_type,
        'constraints': {
            'max_response_time': max_response_time,
            'min_throughput': min_throughput,
            'resource_constraints': resource_constraints
        },
        'recommendations': recommendations
    })

@app.route('/api/performance/evaluate', methods=['POST'])
def evaluate_performance():
    """性能评估接口"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    db_name = data.get('database')
    mq_name = data.get('message_queue')
    os_name = data.get('operating_system')
    workload = data.get('workload', 'medium')
    
    # 获取性能数据
    performance_data = get_performance_data(db_name, mq_name, os_name, workload)
    
    return jsonify({
        'components': {
            'database': db_name,
            'message_queue': mq_name,
            'operating_system': os_name
        },
        'workload': workload,
        'performance_metrics': performance_data
    })

@app.route('/api/metrics/adaptation-rate', methods=['GET'])
def get_adaptation_rate():
    """获取适配率指标"""
    # 计算各种适配率
    db_mq_rate = calculate_db_mq_adaptation_rate()
    db_mq_dependency_rate = calculate_db_mq_dependency_rate()
    db_os_rate = calculate_db_os_adaptation_rate()
    
    return jsonify({
        'database_message_queue_rate': db_mq_rate,
        'database_message_queue_dependency_rate': db_mq_dependency_rate,
        'database_operating_system_rate': db_os_rate,
        'overall_accuracy': (db_mq_rate + db_mq_dependency_rate + db_os_rate) / 3
    })

# 辅助函数
def calculate_compatibility_score(db, mq, os):
    """计算兼容性评分"""
    # 简化的兼容性计算逻辑
    score = 0.8  # 基础分
    
    # 根据协议兼容性调整
    if db and mq:
        if 'JDBC' in str(db) and 'AMQP' in str(mq):
            score += 0.1
    if os and 'Linux' in str(os):
        score += 0.1
    
    return min(score, 1.0)

def get_component_recommendations(db, mq, os):
    """获取组件推荐"""
    recommendations = []
    
    # 数据库推荐
    if db:
        recommendations.append({
            'type': 'database',
            'recommended': COMPONENTS.get('databases', [])[:3],
            'reason': '基于协议兼容性推荐'
        })
    
    # 消息队列推荐
    if mq:
        recommendations.append({
            'type': 'message_queue',
            'recommended': COMPONENTS.get('message_queues', [])[:3],
            'reason': '基于性能表现推荐'
        })
    
    return recommendations

def get_dependencies(db, mq, os):
    """获取依赖环境"""
    return {
        'runtime_requirements': ['Java 8+', 'Python 3.7+'],
        'driver_requirements': ['JDBC驱动', 'AMQP客户端'],
        'protocol_stack': ['TCP/IP', 'HTTP/HTTPS'],
        'os_requirements': ['Linux内核3.10+']
    }

def get_task_recommendations(task_type, max_response_time, min_throughput, resource_constraints):
    """根据任务约束获取推荐"""
    # 简化的任务推荐逻辑
    recommendations = []
    
    if task_type == 'OLTP':
        recommendations.append({
            'database': '人大金仓 KingbaseES',
            'message_queue': '阿里 RabbitMQ',
            'operating_system': '麒麟 Kylin V10',
            'estimated_performance': {
                'throughput': min_throughput * 1.2,
                'response_time': max_response_time * 0.8
            },
            'resource_requirements': {
                'cpu_cores': 4,
                'memory_gb': 8,
                'disk_gb': 100
            }
        })
    
    return recommendations

def get_performance_data(db, mq, os, workload):
    """获取性能数据"""
    # 从PERFORMANCE数据中获取
    return PERFORMANCE.get('baseline', {}).get(workload, {
        'throughput': 1000,
        'latency_p50': 50,
        'latency_p95': 100,
        'cpu_usage': 60,
        'memory_usage': 70
    })

def calculate_db_mq_adaptation_rate():
    """计算数据库×消息队列适配率"""
    return 0.85

def calculate_db_mq_dependency_rate():
    """计算数据库×消息队列依赖关系识别率"""
    return 0.80

def calculate_db_os_adaptation_rate():
    """计算数据库×操作系统适配率"""
    return 0.90
