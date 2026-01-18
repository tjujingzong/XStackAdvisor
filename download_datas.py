"""
从 GitHub 仓库下载指定路径下的所有文件
下载地址: https://github.com/tjujingzong/perftest/tree/main/datas
"""

import os
import requests
import json
from pathlib import Path

# GitHub 仓库信息
REPO_OWNER = "tjujingzong"
REPO_NAME = "perftest"
BRANCH = "main"
TARGET_PATH = "datas"
LOCAL_DIR = "datas"

# GitHub API 基础 URL
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"


def get_file_list(path=""):
    """
    获取 GitHub 仓库指定路径下的所有文件列表
    返回文件路径列表
    """
    url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    params = {"ref": BRANCH}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        items = response.json()
        
        files = []
        for item in items:
            if item["type"] == "file":
                files.append(item["path"])
            elif item["type"] == "dir":
                # 递归获取子目录中的文件
                sub_files = get_file_list(item["path"])
                files.extend(sub_files)
        
        return files
    except requests.exceptions.RequestException as e:
        print(f"获取文件列表失败: {e}")
        return []


def download_file(file_path, local_path):
    """
    下载单个文件
    """
    url = f"{GITHUB_RAW_BASE}/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{file_path}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # 确保本地目录存在
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # 写入文件
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"下载文件失败 {file_path}: {e}")
        return False


def main():
    """
    主函数：下载所有文件
    """
    print(f"开始从 GitHub 下载文件...")
    print(f"仓库: {REPO_OWNER}/{REPO_NAME}")
    print(f"路径: {TARGET_PATH}")
    print(f"保存到: {LOCAL_DIR}")
    print("-" * 50)
    
    # 获取文件列表
    print("正在获取文件列表...")
    files = get_file_list(TARGET_PATH)
    
    if not files:
        print("未找到任何文件！")
        return
    
    print(f"找到 {len(files)} 个文件")
    print("-" * 50)
    
    # 创建本地目录
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    # 下载文件
    success_count = 0
    fail_count = 0
    
    for file_path in files:
        # 计算本地文件路径（移除 TARGET_PATH 前缀）
        relative_path = file_path.replace(f"{TARGET_PATH}/", "", 1)
        local_path = os.path.join(LOCAL_DIR, relative_path)
        
        print(f"下载: {file_path} -> {local_path}")
        
        if download_file(file_path, local_path):
            success_count += 1
            print(f"  ✓ 成功")
        else:
            fail_count += 1
            print(f"  ✗ 失败")
    
    print("-" * 50)
    print(f"下载完成！")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")


if __name__ == "__main__":
    main()

