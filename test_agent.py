#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 DKR Agent 的检索能力
"""
import requests
import json
import sys

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API 端点
API_URL = "http://localhost:8000/agent/ask"

# 测试查询
query = "福建的组织机构在2022年的表现"

print(f"测试查询: {query}\n")
print("=" * 80)

try:
    # 发送请求（增加超时时间到 300 秒）
    response = requests.post(
        API_URL,
        params={"query": query},
        timeout=300
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应头: {response.headers}")
    print(f"\n响应内容:")
    print("=" * 80)
    
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"错误: {response.text}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

