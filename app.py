"""
信创组件适配评估系统 - 主应用入口
提供基于组件和基于任务的适配评估API接口
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 加载JSON数据
def load_data():
    """加载组件数据"""
    try:
        # 组件数据从 datas 目录加载（真实数据）
        components_path = 'datas/components.json'
        
        # 向后兼容：如果 datas/components.json 不存在，尝试从 fake-data 或 data 加载
        if not os.path.exists(components_path):
            if os.path.exists('fake-data/components.json'):
                components_path = 'fake-data/components.json'
            elif os.path.exists('data/components.json'):
                components_path = 'data/components.json'
        
        components = {}
        
        if os.path.exists(components_path):
            with open(components_path, 'r', encoding='utf-8') as f:
                components = json.load(f)
        
        return components
    except Exception as e:
        print(f"加载数据文件失败: {e}")
        return {}

# 全局数据
COMPONENTS = load_data()

# 导入路由
from routes import *

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
