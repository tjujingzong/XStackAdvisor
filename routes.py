"""
信创组件适配评估系统 - API路由
"""

from flask import jsonify, request
from app import app, COMPONENTS
import json
import os
import pandas as pd
import pathlib
from typing import Optional, List, Dict
from normalize_metrics import NormalizedMetrics

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
    """基于任务的适配评估（基于CSV真实数据）"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    # 获取任务约束
    task_type = data.get('task_type', 'OLTP')
    max_response_time = data.get('max_response_time', 1000)  # ms
    min_throughput = data.get('min_throughput', 1000)  # TPS
    resource_constraints = data.get('resource_constraints', {})
    
    # 从CSV数据中查找满足条件的组件组合
    recommendations = get_task_recommendations_from_csv(
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
    """性能评估接口（基于CSV真实数据）"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    db_name = data.get('database')
    mq_name = data.get('message_queue')
    os_name = data.get('operating_system')
    
    # 从CSV数据中获取性能数据
    performance_data = get_performance_data_from_csv(db_name, mq_name)
    
    return jsonify({
        'components': {
            'database': db_name,
            'message_queue': mq_name,
            'operating_system': os_name
        },
        'performance_metrics': performance_data
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

def get_task_recommendations_from_csv(task_type, max_response_time, min_throughput, resource_constraints):
    """根据任务约束从CSV数据中获取推荐"""
    recommendations = []
    data_dir = pathlib.Path('datas')
    
    if not data_dir.exists():
        return recommendations
    
    # 查找数据库CSV文件
    db_csv = data_dir / "results.csv"
    if not db_csv.exists():
        db_csv = find_latest_csv(data_dir, "*_kbbench_results_*.csv")
    if db_csv is None:
        db_csv = find_latest_csv(data_dir, "*kbbench*.csv")
    
    # 查找消息队列CSV文件
    mq_csv = find_latest_csv(data_dir, "*perftest_summary_*.csv")
    
    db_data = None
    mq_data = None
    
    # 加载数据库数据
    if db_csv and db_csv.exists():
        try:
            df_db = pd.read_csv(db_csv)
            # 过滤满足条件的记录：延迟 <= max_response_time, TPS >= min_throughput
            valid_db = df_db[
                (df_db['latency_ms_avg'] <= max_response_time) &
                (df_db['tps_excluding'] >= min_throughput) &
                (df_db['return_code'] == 0)
            ]
            if len(valid_db) > 0:
                # 选择最佳性能记录（最高TPS）
                best_db = valid_db.loc[valid_db['tps_excluding'].idxmax()]
                db_data = {
                    'component': db_csv.name.split('_')[0] if '_' in db_csv.name else 'Unknown',
                    'tps': float(best_db['tps_excluding']),
                    'latency_ms': float(best_db['latency_ms_avg']),
                    'cpu_usage': float(best_db.get('avg_cpu_percent', 0)),
                    'memory_usage': float(best_db.get('avg_memory_percent', 0)),
                    'memory_gb': float(best_db.get('avg_memory_used_gb', 0))
                }
        except Exception as e:
            print(f"加载数据库CSV数据失败: {e}")
    
    # 加载消息队列数据
    if mq_csv and mq_csv.exists():
        try:
            df_mq = pd.read_csv(mq_csv)
            # 过滤满足条件的记录：延迟 <= max_response_time, 吞吐量 >= min_throughput
            valid_mq = df_mq[
                (df_mq['worst_p95_ms'] <= max_response_time) &
                (df_mq['avg_received_msg_s'] >= min_throughput) &
                (df_mq['success'] == True)
            ]
            if len(valid_mq) > 0:
                # 选择最佳性能记录（最高吞吐量）
                best_mq = valid_mq.loc[valid_mq['avg_received_msg_s'].idxmax()]
                mq_data = {
                    'component': mq_csv.name.split('_')[0] if '_' in mq_csv.name else 'Unknown',
                    'throughput': float(best_mq['avg_received_msg_s']),
                    'latency_p95_ms': float(best_mq['worst_p95_ms']),
                    'cpu_usage': float(best_mq.get('avg_cpu_percent', 0)),
                    'memory_usage': float(best_mq.get('avg_memory_percent', 0)),
                    'memory_gb': float(best_mq.get('avg_memory_used_gb', 0))
                }
        except Exception as e:
            print(f"加载消息队列CSV数据失败: {e}")
    
    # 构建推荐结果
    if db_data and mq_data:
        recommendations.append({
            'database': db_data['component'],
            'message_queue': mq_data['component'],
            'operating_system': '麒麟 Kylin V10',  # 从components.json获取或默认值
            'estimated_performance': {
                'throughput': db_data['tps'],
                'response_time': db_data['latency_ms'],
                'message_queue_throughput': mq_data['throughput'],
                'message_queue_latency_p95': mq_data['latency_p95_ms']
            },
            'resource_requirements': {
                'cpu_cores': 4,  # 可以从CSV数据中提取或使用默认值
                'memory_gb': max(db_data.get('memory_gb', 0), mq_data.get('memory_gb', 0)) or 8,
                'disk_gb': 100
            },
            'actual_metrics': {
                'database_cpu_usage': db_data['cpu_usage'],
                'database_memory_usage': db_data['memory_usage'],
                'message_queue_cpu_usage': mq_data['cpu_usage'],
                'message_queue_memory_usage': mq_data['memory_usage']
            }
        })
    
    return recommendations

def get_performance_data_from_csv(db, mq):
    """从CSV数据中获取性能数据"""
    result = {}
    data_dir = pathlib.Path('datas')
    
    if not data_dir.exists():
        return result
    
    # 获取数据库性能数据
    if db:
        db_csv = data_dir / "results.csv"
        if not db_csv.exists():
            db_csv = find_latest_csv(data_dir, "*_kbbench_results_*.csv")
        if db_csv is None:
            db_csv = find_latest_csv(data_dir, "*kbbench*.csv")
        
        if db_csv and db_csv.exists():
            try:
                df_db = pd.read_csv(db_csv)
                # 过滤有效记录
                valid_db = df_db[df_db['return_code'] == 0]
                if len(valid_db) > 0:
                    # 计算平均值或使用最佳值
                    best_db = valid_db.loc[valid_db['tps_excluding'].idxmax()]
                    result['database'] = {
                        'throughput_tps': float(best_db['tps_excluding']),
                        'latency_ms_avg': float(best_db['latency_ms_avg']),
                        'cpu_usage_percent': float(best_db.get('avg_cpu_percent', 0)),
                        'memory_usage_percent': float(best_db.get('avg_memory_percent', 0)),
                        'memory_used_gb': float(best_db.get('avg_memory_used_gb', 0))
                    }
            except Exception as e:
                print(f"加载数据库性能数据失败: {e}")
    
    # 获取消息队列性能数据
    if mq:
        mq_csv = find_latest_csv(data_dir, "*perftest_summary_*.csv")
        
        if mq_csv and mq_csv.exists():
            try:
                df_mq = pd.read_csv(mq_csv)
                # 过滤成功记录
                valid_mq = df_mq[df_mq['success'] == True]
                if len(valid_mq) > 0:
                    # 选择最佳性能记录
                    best_mq = valid_mq.loc[valid_mq['avg_received_msg_s'].idxmax()]
                    result['message_queue'] = {
                        'throughput_msg_per_sec': float(best_mq['avg_received_msg_s']),
                        'latency_p95_ms': float(best_mq['worst_p95_ms']),
                        'cpu_usage_percent': float(best_mq.get('avg_cpu_percent', 0)),
                        'memory_usage_percent': float(best_mq.get('avg_memory_percent', 0)),
                        'memory_used_gb': float(best_mq.get('avg_memory_used_gb', 0))
                    }
            except Exception as e:
                print(f"加载消息队列性能数据失败: {e}")
    
    return result

# 真实环境数据读取函数
def find_latest_csv(directory: pathlib.Path, pattern: str) -> Optional[pathlib.Path]:
    """查找最新的匹配CSV文件"""
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)

def load_db_csv_data(component: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    加载数据库测试结果CSV数据
    
    Args:
        component: 组件名称过滤（如 "KingbaseES"）
        limit: 返回记录数限制
    
    Returns:
        数据库测试结果列表
    """
    data_dir = pathlib.Path('datas')
    if not data_dir.exists():
        return []
    
    # 查找数据库测试结果文件
    db_csv = data_dir / "results.csv"
    if not db_csv.exists():
        db_csv = find_latest_csv(data_dir, "*_kbbench_results_*.csv")
    if db_csv is None:
        db_csv = find_latest_csv(data_dir, "*kbbench*.csv")
    
    if db_csv is None or not db_csv.exists():
        return []
    
    try:
        df = pd.read_csv(db_csv)
        
        # 如果指定了组件名称，进行过滤
        if component:
            # 从文件名或数据中匹配组件名
            if component.lower() not in db_csv.name.lower():
                return []
        
        # 处理可选字段：将 NaN 和空字符串转换为 None
        df = df.replace([pd.NA, pd.NaT, ''], None)
        df = df.where(pd.notnull(df), None)
        
        # 限制返回记录数
        if len(df) > limit:
            df = df.head(limit)
        
        # 转换为字典列表
        records = df.to_dict('records')
        
        # 清理数据：移除空字符串和 None 值的字段（可选字段）
        # 但保留数字 0 和 False 值
        cleaned_records = []
        for record in records:
            cleaned = {}
            for k, v in record.items():
                # 保留所有非 None 和非空字符串的值
                if v is not None and v != '':
                    cleaned[k] = v
            cleaned_records.append(cleaned)
        
        return cleaned_records
    except Exception as e:
        print(f"加载数据库CSV数据失败: {e}")
        return []

def load_mq_csv_data(component: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    加载消息队列测试结果CSV数据
    
    Args:
        component: 组件名称过滤（如 "RabbitMQ"）
        limit: 返回记录数限制
    
    Returns:
        消息队列测试结果列表
    """
    data_dir = pathlib.Path('datas')
    if not data_dir.exists():
        return []
    
    # 查找消息队列测试结果文件
    mq_csv = find_latest_csv(data_dir, "*perftest_summary_*.csv")
    
    if mq_csv is None or not mq_csv.exists():
        return []
    
    try:
        df = pd.read_csv(mq_csv)
        
        # 如果指定了组件名称，进行过滤
        if component:
            # 从文件名或数据中匹配组件名
            if component.lower() not in mq_csv.name.lower():
                return []
        
        # 处理可选字段：将 NaN 和空字符串转换为 None
        df = df.replace([pd.NA, pd.NaT, ''], None)
        df = df.where(pd.notnull(df), None)
        
        # 限制返回记录数
        if len(df) > limit:
            df = df.head(limit)
        
        # 转换为字典列表
        records = df.to_dict('records')
        
        # 清理数据：移除空字符串和 None 值的字段（可选字段）
        # 但保留数字 0 和 False 值
        cleaned_records = []
        for record in records:
            cleaned = {}
            for k, v in record.items():
                # 保留所有非 None 和非空字符串的值
                if v is not None and v != '':
                    cleaned[k] = v
            cleaned_records.append(cleaned)
        
        return cleaned_records
    except Exception as e:
        print(f"加载消息队列CSV数据失败: {e}")
        return []

@app.route('/api/capacity/extrapolation', methods=['POST'])
def capacity_extrapolation():
    """容量外推接口：根据组件名称和目标性能计算所需CPU和内存"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    component_name = data.get('component_name')
    component_type = data.get('component_type')  # 'DB' 或 'MQ'
    target_tps = data.get('target_tps')  # 数据库目标TPS
    target_msg_per_sec = data.get('target_msg_per_sec')  # 消息队列目标消息/秒
    max_latency_ms = data.get('max_latency_ms', 1000)  # 最大延迟（ms）
    test_cpu_cores = data.get('test_cpu_cores', 4)  # 测试环境CPU核心数
    test_memory_gb = data.get('test_memory_gb', 4.0)  # 测试环境内存GB
    
    if not component_name or not component_type:
        return jsonify({'error': 'component_name 和 component_type 是必需的'}), 400
    
    if component_type == 'DB' and not target_tps:
        return jsonify({'error': '数据库类型需要提供 target_tps'}), 400
    
    if component_type == 'MQ' and not target_msg_per_sec:
        return jsonify({'error': '消息队列类型需要提供 target_msg_per_sec'}), 400
    
    try:
        # 加载归一化数据
        normalizer = NormalizedMetrics(cpu_cores=test_cpu_cores, memory_gb=test_memory_gb)
        
        # 直接从CSV文件加载数据并归一化
        normalized_data = []
        data_dir = pathlib.Path('datas')
        
        if component_type == 'DB':
            # 查找数据库CSV文件
            db_csv = data_dir / "results.csv"
            if not db_csv.exists():
                db_csv = find_latest_csv(data_dir, "*_kbbench_results_*.csv")
            if db_csv is None:
                db_csv = find_latest_csv(data_dir, "*kbbench*.csv")
            
            if db_csv and db_csv.exists():
                # 检查组件名称是否匹配
                if component_name.lower() not in db_csv.name.lower():
                    return jsonify({'error': f'未找到组件 {component_name} 的测试数据文件'}), 404
                
                df = pd.read_csv(db_csv)
                normalized_df = normalizer.normalize_db_metrics(df, component_name)
                normalized_data.append(normalized_df)
        elif component_type == 'MQ':
            # 查找消息队列CSV文件
            mq_csv = find_latest_csv(data_dir, "*perftest_summary_*.csv")
            
            if mq_csv and mq_csv.exists():
                # 检查组件名称是否匹配
                if component_name.lower() not in mq_csv.name.lower():
                    return jsonify({'error': f'未找到组件 {component_name} 的测试数据文件'}), 404
                
                df = pd.read_csv(mq_csv)
                normalized_df = normalizer.normalize_mq_metrics(df, component_name)
                normalized_data.append(normalized_df)
        
        if not normalized_data:
            return jsonify({'error': f'未找到组件 {component_name} 的测试数据'}), 404
        
        # 合并归一化数据
        normalized_df = pd.concat(normalized_data, ignore_index=True)
        
        # 构建目标SLO
        if component_type == 'DB':
            target_slo = {
                'component_type': 'DB',
                'target_tps': target_tps,
                'max_latency_ms': max_latency_ms
            }
        else:
            target_slo = {
                'component_type': 'MQ',
                'target_msg_per_sec': target_msg_per_sec,
                'max_p95_ms': max_latency_ms
            }
        
        # 执行容量外推
        recommendations = normalizer.generate_capacity_extrapolation(normalized_df, target_slo)
        
        if len(recommendations) == 0:
            return jsonify({
                'error': '未找到满足SLO要求的基准数据',
                'component_name': component_name,
                'component_type': component_type
            }), 404
        
        # 转换为字典格式返回
        result = recommendations.iloc[0].to_dict()
        
        return jsonify({
            'component_name': component_name,
            'component_type': component_type,
            'recommendations': {
                'required_cpu_cores': int(result.get('required_cpu_cores', 0)),
                'required_memory_gb': int(result.get('required_memory_gb', 0)),
                'estimated_latency_ms': result.get('estimated_latency_ms') if component_type == 'DB' else result.get('estimated_p95_ms'),
                'baseline_metrics': {
                    'tps_per_core': result.get('baseline_tps_per_core') if component_type == 'DB' else None,
                    'msg_per_sec_per_core': result.get('baseline_msg_per_sec_per_core') if component_type == 'MQ' else None,
                    'cpu_utilization_pct': result.get('baseline_cpu_utilization_pct'),
                    'memory_utilization_pct': result.get('baseline_memory_utilization_pct')
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'容量外推计算失败: {str(e)}'}), 500
