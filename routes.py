"""
信创组件适配评估系统 - API路由
"""

from flask import jsonify, request
from app import app, COMPONENTS
import pandas as pd
import pathlib
import json
from typing import Optional

# ── 真值表加载 ──────────────────────────────────────────────────────────────

_GROUND_TRUTH = None

def _load_ground_truth() -> dict:
    global _GROUND_TRUTH
    if _GROUND_TRUTH is not None:
        return _GROUND_TRUTH
    gt_path = pathlib.Path('datas/ground_truth.json')
    if gt_path.exists():
        with open(gt_path, 'r', encoding='utf-8') as f:
            _GROUND_TRUTH = json.load(f)
    else:
        _GROUND_TRUTH = {}
    return _GROUND_TRUTH


def _gt_name_match(gt_dict: dict, name: str):
    """在真值表字典中查找键：先精确匹配，再前缀/子串匹配。"""
    if name in gt_dict:
        return gt_dict[name]
    for key, val in gt_dict.items():
        if key in name or name in key:
            return val
    return None


# ── 准确性计算 ──────────────────────────────────────────────────────────────

def calculate_component_accuracy(
    db_name: Optional[str],
    mq_name: Optional[str],
    os_name: Optional[str],
    is_compatible: bool,
    selected_components: dict,
) -> Optional[float]:
    """
    基于组件适配评估的准确性，三个维度加权：
      - DB×MQ 兼容性判断  40%
      - DB×OS 兼容性判断  40%
      - 依赖关键词识别率  20%
    """
    gt = _load_ground_truth()
    if not gt:
        return None

    scores, weights = [], []

    # 1. DB×MQ 兼容性
    if db_name and mq_name:
        db_mq_row = _gt_name_match(gt.get('db_mq_compatibility', {}), db_name)
        if db_mq_row is not None:
            gt_val = _gt_name_match(db_mq_row, mq_name)
            if gt_val is not None:
                scores.append(1.0 if is_compatible == gt_val else 0.0)
                weights.append(0.4)

    # 2. DB×OS 兼容性
    if db_name and os_name:
        db_os_row = _gt_name_match(gt.get('db_os_compatibility', {}), db_name)
        if db_os_row is not None:
            gt_val = _gt_name_match(db_os_row, os_name)
            if gt_val is not None:
                scores.append(1.0 if is_compatible == gt_val else 0.0)
                weights.append(0.4)

    # 3. 依赖关键词识别率
    dep_kw = gt.get('dependency_keywords', {})
    dep_scores = []
    for comp_type, comp_data in selected_components.items():
        required = dep_kw.get(comp_type, [])
        if not required:
            continue
        deps = comp_data.get('dependencies', [])
        deps_text = ' '.join(deps).lower()
        matched = sum(1 for kw in required if kw.lower() in deps_text)
        dep_scores.append(matched / len(required))
    if dep_scores:
        scores.append(sum(dep_scores) / len(dep_scores))
        weights.append(0.2)

    if not scores:
        return None

    total_w = sum(weights)
    return round(sum(s * w for s, w in zip(scores, weights)) / total_w, 3)


def calculate_task_accuracy(task_type: str, recommendations: list) -> Optional[float]:
    """
    基于任务适配评估的准确性：
    推荐组合中 DB / MQ / OS / 中间件均在真值表兼容列表内的比例。
    """
    gt = _load_ground_truth()
    if not gt or not recommendations:
        return None

    task_gt = gt.get('task_recommendations', {}).get(task_type)
    if not task_gt:
        return None

    compat_db  = task_gt.get('compatible_databases', [])
    compat_mq  = task_gt.get('compatible_mq', [])
    compat_os  = task_gt.get('compatible_os', [])
    compat_mw  = task_gt.get('compatible_middlewares', [])

    correct = 0
    for rec in recommendations:
        db_ok = not compat_db  or rec.get('database')          in compat_db
        mq_ok = not compat_mq  or rec.get('message_queue')     in compat_mq
        os_ok = not compat_os  or rec.get('operating_system')  in compat_os
        mw_ok = not compat_mw  or rec.get('middleware')        in compat_mw
        if db_ok and mq_ok and os_ok and mw_ok:
            correct += 1

    return round(correct / len(recommendations), 3)

@app.route('/api/adaptation/component-based', methods=['POST'])
def component_based_adaptation():
    """基于组件的适配评估（要求操作系统必填，其余组件可选：数据库 / 消息队列 / 中间件）"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    # 获取输入参数
    target_db = data.get('target_database')
    target_mq = data.get('target_message_queue')
    target_os = data.get('target_operating_system')
    target_middleware = data.get('target_middleware')

    # 操作系统为必填参数
    if not target_os:
        return jsonify({'error': 'target_operating_system 为必填参数'}), 400

    # 查找具体组件信息
    db_comp = _find_component_by_name('databases', target_db) if target_db else None
    mq_comp = _find_component_by_name('message_queues', target_mq) if target_mq else None
    mw_comp = _find_component_by_name('middlewares', target_middleware) if target_middleware else None
    os_comp = _find_component_by_name('operating_systems', target_os)
    
    # 兼容性评分：针对用户选择的组合
    compatibility_score = calculate_compatibility_score(db_comp, mq_comp, os_comp)
    
    # 推荐相关组件（基于操作系统和当前已选组件）
    recommendations = get_component_recommendations(
        target_db,
        target_mq,
        target_os,
        target_middleware=target_middleware,
    )
    
    # 获取选中组件的详细信息（包含依赖项）
    selected_components = {}
    if db_comp:
        selected_components['database'] = {
            'id': db_comp.get('id'),
            'name': db_comp.get('name'),
            'version': db_comp.get('version'),
            'vendor': db_comp.get('vendor'),
            'protocol': db_comp.get('protocol'),
            'dependencies': db_comp.get('dependencies', []),
        }
    if mq_comp:
        selected_components['message_queue'] = {
            'id': mq_comp.get('id'),
            'name': mq_comp.get('name'),
            'version': mq_comp.get('version'),
            'vendor': mq_comp.get('vendor'),
            'protocol': mq_comp.get('protocol'),
            'dependencies': mq_comp.get('dependencies', []),
        }
    if mw_comp:
        selected_components['middleware'] = {
            'id': mw_comp.get('id'),
            'name': mw_comp.get('name'),
            'version': mw_comp.get('version'),
            'vendor': mw_comp.get('vendor'),
            'protocol': mw_comp.get('protocol'),
            'dependencies': mw_comp.get('dependencies', []),
        }
    if os_comp:
        selected_components['operating_system'] = {
            'id': os_comp.get('id'),
            'name': os_comp.get('name'),
            'version': os_comp.get('version'),
            'vendor': os_comp.get('vendor'),
            'architecture': os_comp.get('architecture'),
            'kernel_version': os_comp.get('kernel_version'),
            'dependencies': os_comp.get('dependencies', []),
        }
    
    accuracy = calculate_component_accuracy(
        db_name=target_db,
        mq_name=target_mq,
        os_name=target_os,
        is_compatible=compatibility_score > 0.7,
        selected_components=selected_components,
    )

    return jsonify({
        'compatibility_score': round(compatibility_score, 3),
        'is_compatible': compatibility_score > 0.7,
        'accuracy': accuracy,
        'selected_components': selected_components,
        'recommendations': recommendations,
        'dependencies': get_dependencies(
            db_comp or target_db,
            mq_comp or target_mq,
            os_comp or target_os,
            mw_comp or target_middleware,
        ),
    })

@app.route('/api/adaptation/task-based', methods=['POST'])
def task_based_adaptation():
    """基于任务的适配评估（当前使用假的评估数据；不依赖CSV）"""
    data = request.get_json()

    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400

    task_type = data.get('task_type', 'OLTP')
    max_response_time = data.get('max_response_time', 1000)  # ms
    min_throughput = data.get('min_throughput', 1000)  # TPS
    resource_constraints = data.get('resource_constraints', {})

    recommendations = get_task_recommendations_mock(
        task_type=task_type,
        max_response_time=max_response_time,
        min_throughput=min_throughput,
        resource_constraints=resource_constraints,
    )

    accuracy = calculate_task_accuracy(task_type, recommendations)

    return jsonify({
        'task_type': task_type,
        'constraints': {
            'max_response_time': max_response_time,
            'min_throughput': min_throughput,
            'resource_constraints': resource_constraints,
        },
        'accuracy': accuracy,
        'recommendations': recommendations,
    })


def calculate_compatibility_score(db, mq, os):
    """计算兼容性评分（基于协议和操作系统兼容标签）"""
    score = 0.8  # 基础分

    # 提取协议和名称信息（兼容字符串或组件字典）
    def _extract_protocol(comp) -> str:
        if isinstance(comp, dict):
            return str(comp.get('protocol', ''))
        return str(comp) if comp else ''

    def _extract_os_name(comp) -> str:
        if isinstance(comp, dict):
            return str(comp.get('name', ''))
        return str(comp) if comp else ''

    def _extract_os_tags(comp):
        if isinstance(comp, dict):
            return comp.get('compatibility_tags', []) or []
        return []

    db_protocol = _extract_protocol(db)
    mq_protocol = _extract_protocol(mq)
    os_name = _extract_os_name(os)
    os_tags = _extract_os_tags(os)

    # 根据协议兼容性调整：JDBC/ODBC + AMQP 组合更优
    if db_protocol and mq_protocol:
        if (('JDBC' in db_protocol) or ('ODBC' in db_protocol)) and ('AMQP' in mq_protocol):
            score += 0.1

    # 根据操作系统及其兼容标签调整
    if os_name or os_tags:
        if 'Linux' in os_name or any(tag in ('Linux', 'Debian', 'Ubuntu') for tag in os_tags):
            score += 0.1

    return min(score, 1.0)


def get_component_recommendations(
    target_db: Optional[str],
    target_mq: Optional[str],
    target_os: str,
    target_middleware: Optional[str] = None,
):
    """
    获取组件推荐（逻辑对称、简洁）：
    - 操作系统必选
    - 针对用户「未选择」的组件类型返回推荐：
      - 未选数据库 => 推荐数据库
      - 未选消息队列 => 推荐消息队列
      - 未选中间件   => 推荐中间件
    """
    recommendations = []

    os_comp = _find_component_by_name('operating_systems', target_os)
    selected_db = _find_component_by_name('databases', target_db) if target_db else None
    selected_mq = _find_component_by_name('message_queues', target_mq) if target_mq else None
    selected_mw = _find_component_by_name('middlewares', target_middleware) if target_middleware else None

    # 数据库推荐：只有在用户没有选择数据库时才推荐
    if not selected_db:
        db_candidates = []
        for db in COMPONENTS.get('databases', []):
            score = calculate_compatibility_score(db, selected_mq, os_comp)
            db_candidates.append({
                'id': db.get('id'),
                'name': db.get('name'),
                'vendor': db.get('vendor'),
                'version': db.get('version'),
                'protocol': db.get('protocol'),
                'dependencies': db.get('dependencies', []),
                'score': round(score, 3),
            })

        db_candidates.sort(key=lambda x: x['score'], reverse=True)
        if db_candidates:
            recommendations.append({
                'type': 'database',
                'recommended': [
                    {
                        **db_item,
                        'reason': '基于与当前操作系统和已选组件的兼容性评分',
                    }
                    for db_item in db_candidates[:3]
                ],
            })

    # 消息队列推荐：只有在用户没有选择消息队列时才推荐
    if not selected_mq:
        mq_candidates = []
        for mq in COMPONENTS.get('message_queues', []):
            score = calculate_compatibility_score(selected_db, mq, os_comp)
            mq_candidates.append({
                'id': mq.get('id'),
                'name': mq.get('name'),
                'vendor': mq.get('vendor'),
                'version': mq.get('version'),
                'protocol': mq.get('protocol'),
                'dependencies': mq.get('dependencies', []),
                'score': round(score, 3),
            })

        mq_candidates.sort(key=lambda x: x['score'], reverse=True)
        if mq_candidates:
            recommendations.append({
                'type': 'message_queue',
                'recommended': [
                    {
                        **mq_item,
                        'reason': '基于与当前操作系统和已选组件的兼容性评分',
                    }
                    for mq_item in mq_candidates[:3]
                ],
            })

    # 中间件推荐：只有在用户没有选择中间件时才推荐
    if not selected_mw:
        mw_candidates = []
        for mw in COMPONENTS.get('middlewares', []):
            # 复用数据库 + 消息类组件 + 操作系统的评分逻辑
            score = calculate_compatibility_score(selected_db, mw, os_comp)
            mw_candidates.append({
                'id': mw.get('id'),
                'name': mw.get('name'),
                'vendor': mw.get('vendor'),
                'version': mw.get('version'),
                'protocol': mw.get('protocol'),
                'dependencies': mw.get('dependencies', []),
                'score': round(score, 3),
            })

        mw_candidates.sort(key=lambda x: x['score'], reverse=True)
        if mw_candidates:
            recommendations.append({
                'type': 'middleware',
                'recommended': [
                    {
                        **mw_item,
                        'reason': '基于与当前操作系统和已选组件的兼容性评分',
                    }
                    for mw_item in mw_candidates[:3]
                ],
            })

    return recommendations


def get_dependencies(db, mq, os, middleware=None):
    """获取依赖环境：
    - 避免与 selected_components 中的组件依赖重复
    - 仅在传入的是“名称字符串”等简单形式时，补充通用依赖
    - 始终补充通用运行环境依赖（runtime）
    """
    dependencies = []

    def _name(comp):
        if isinstance(comp, dict):
            return comp.get('name')
        return comp

    # 对于 dict（已经在 selected_components 中返回了详细信息）的组件，
    # 这里不再重复列出；只有在传入的是字符串等简单形式时才补充一份通用依赖。

    if db and not isinstance(db, dict):
        dependencies.append({
            'component_type': 'database',
            'component_name': _name(db),
            'items': [
                '数据库 JDBC/ODBC 驱动',
                '连接池配置（如 HikariCP、Druid）',
                '数据库客户端工具和监控组件',
            ],
        })

    if mq and not isinstance(mq, dict):
        dependencies.append({
            'component_type': 'message_queue',
            'component_name': _name(mq),
            'items': [
                'AMQP/JMS 客户端 SDK',
                '消息队列管理控制台',
                '网络端口和安全策略配置',
            ],
        })

    if middleware and not isinstance(middleware, dict):
        dependencies.append({
            'component_type': 'middleware',
            'component_name': _name(middleware),
            'items': [
                'JMS/AMQP 客户端 SDK',
                '中间件管理控制台',
                '网络端口和安全策略配置',
            ],
        })

    if os and not isinstance(os, dict):
        dependencies.append({
            'component_type': 'operating_system',
            'component_name': _name(os),
            'items': [
                'Linux 内核 3.10+ 或等效版本',
                'glibc 等基础运行时库',
                '系统调优参数（文件句柄数、网络缓冲区等）',
            ],
        })

    # 通用运行环境依赖
    dependencies.append({
        'component_type': 'runtime',
        'component_name': '通用运行环境',
        'items': [
            'Python 3.7+',
            'Java 8+',
            'TCP/IP 网络和 HTTP/HTTPS 协议栈',
        ],
    })

    return dependencies

import uuid
import time
import random

def get_task_recommendations_mock(task_type, max_response_time, min_throughput, resource_constraints):
    """
    生成模拟的推荐方案逻辑，包含数据库、消息队列和中间件
    """
    recommendations = []
    
    # 从全局 COMPONENTS 中获取真实存在的组件名称，以增强真实感
    db_names = [d['name'] for d in COMPONENTS.get('databases', [])] or ["达梦数据库", "人大金仓 KingbaseES"]
    mq_names = [m['name'] for m in COMPONENTS.get('message_queues', [])] or ["阿里 RabbitMQ", "宝兰德 BES MQ"]
    mw_names = [w['name'] for w in COMPONENTS.get('middlewares', [])] or ["东方通 TongLink/Q", "阿里 Tengine"]
    os_names = [o['name'] for o in COMPONENTS.get('operating_systems', [])] or ["麒麟 Kylin", "统信 UOS"]

    # 生成 3 个推荐方案
    for i in range(3):
        db = random.choice(db_names)
        mq = random.choice(mq_names)
        mw = random.choice(mw_names)
        os_name = random.choice(os_names)

        # 模拟性能指标：确保符合约束
        perf_throughput = min_throughput + random.randint(100, 500)
        perf_latency = max_response_time - random.randint(10, 100)
        score = round(random.uniform(0.85, 0.98), 2)

        recommendations.append({
            'id': f"plan-{i+1}",
            'name': f"方案 {i+1}: {task_type} 优化组合",
            'database': db,
            'message_queue': mq,
            'middleware': mw,
            'operating_system': os_name,
            'score': score,
            'estimated_performance': {
                'throughput': perf_throughput,
                'response_time_ms': perf_latency,
                'score': score
            },
            'resource_requirements': {
                'cpu_cores': resource_constraints.get('max_cpu_cores', 8),
                'memory_gb': resource_constraints.get('max_memory_gb', 16),
                'storage_gb': 100
            },
        })

    # 按评分从高到低排序
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    return recommendations

def get_task_recommendations_from_csv(task_type, max_response_time, min_throughput, resource_constraints):
    """
    根据任务约束从CSV数据中获取推荐
    - 支持任务类型：OLTP、ALTP（当前按相同规则过滤，只是类型标识不同）
    - 推荐方案尽量给出三个组合
    """
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
    
    db_candidates = []
    mq_candidates = []
    
    # 加载数据库数据：按 TPS 从高到低取前 3 条
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
                valid_db = valid_db.sort_values(by='tps_excluding', ascending=False).head(3)
                for _, row in valid_db.iterrows():
                    db_candidates.append({
                        'component': db_csv.name.split('_')[0] if '_' in db_csv.name else 'Unknown',
                        'tps': float(row['tps_excluding']),
                        'latency_ms': float(row['latency_ms_avg']),
                        'cpu_usage': float(row.get('avg_cpu_percent', 0)),
                        'memory_usage': float(row.get('avg_memory_percent', 0)),
                        'memory_gb': float(row.get('avg_memory_used_gb', 0))
                    })
        except Exception as e:
            print(f"加载数据库CSV数据失败: {e}")
    
    # 加载消息队列数据：按吞吐量从高到低取前 3 条
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
                valid_mq = valid_mq.sort_values(by='avg_received_msg_s', ascending=False).head(3)
                for _, row in valid_mq.iterrows():
                    mq_candidates.append({
                        'component': mq_csv.name.split('_')[0] if '_' in mq_csv.name else 'Unknown',
                        'throughput': float(row['avg_received_msg_s']),
                        'latency_p95_ms': float(row['worst_p95_ms']),
                        'cpu_usage': float(row.get('avg_cpu_percent', 0)),
                        'memory_usage': float(row.get('avg_memory_percent', 0)),
                        'memory_gb': float(row.get('avg_memory_used_gb', 0))
                    })
        except Exception as e:
            print(f"加载消息队列CSV数据失败: {e}")
    
    # 构建推荐结果：最多返回 3 个组合
    count = min(3, len(db_candidates), len(mq_candidates))
    for i in range(count):
        db_data = db_candidates[i]
        mq_data = mq_candidates[i]

        # 计算综合评分（基于性能指标）
        # 评分规则：TPS越高越好，延迟越低越好，资源占用越低越好
        tps_score = min(db_data['tps'] / min_throughput, 2.0) * 0.3  # TPS权重30%
        latency_score = max(0, 2.0 - db_data['latency_ms'] / max_response_time) * 0.3  # 延迟权重30%
        mq_throughput_score = min(mq_data['throughput'] / min_throughput, 2.0) * 0.2  # MQ吞吐量权重20%
        resource_score = max(0, 2.0 - (db_data['cpu_usage'] + mq_data['cpu_usage']) / 200) * 0.2  # 资源占用权重20%

        score = (tps_score + latency_score + mq_throughput_score + resource_score) * 0.5  # 归一化到0-1

        recommendations.append({
            'database': db_data['component'],
            'message_queue': mq_data['component'],
            'operating_system': '麒麟 Kylin V10',  # 从components.json获取或默认值
            'score': round(score, 3),  # 添加评分字段
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

    # 按评分从高到低排序
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    return recommendations


def _find_component_by_name(category: str, name: Optional[str]):
    """在 COMPONENTS 中按名称查找组件"""
    if not name:
        return None
    for comp in COMPONENTS.get(category, []):
        if comp.get('name') == name:
            return comp
    return None


# 真实环境数据读取函数
def find_latest_csv(directory: pathlib.Path, pattern: str) -> Optional[pathlib.Path]:
    """查找最新的匹配CSV文件"""
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)

