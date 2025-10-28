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
    """加载组件和性能数据"""
    try:
        with open('data/components.json', 'r', encoding='utf-8') as f:
            components = json.load(f)
        with open('data/performance.json', 'r', encoding='utf-8') as f:
            performance = json.load(f)
        return components, performance
    except FileNotFoundError:
        return {}, {}

# 全局数据
COMPONENTS, PERFORMANCE = load_data()

# 导入路由
from routes import *

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
