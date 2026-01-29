#!/usr/bin/env python3
"""
获取部署日志
"""

import os
import sys
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "STUDENT_PORTAL_BASE_URL",
    "https://space.ai-builders.com/backend"
)

API_KEY = (
    os.getenv("STUDENT_PORTAL_API_KEY") or
    os.getenv("AI_BUILDER_TOKEN") or
    os.getenv("AI_BUILDER_API_TOKEN") or
    os.getenv("SUPER_MIND_API_KEY") or
    os.getenv("OPENAI_API_KEY")
)

def get_deployment_logs(service_name: str):
    """获取部署日志"""
    if not API_KEY:
        print("❌ 未找到 API Key")
        return None
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Get deployment logs
    url = f"{API_BASE_URL}/v1/deployments/{service_name}/logs"
    
    try:
        print(f"🔍 获取部署日志: {service_name}")
        print(f"📡 API URL: {url}")
        print()
        
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 日志获取成功")
                print()
                print("📋 部署日志:")
                print("-" * 60)
                logs = data.get("logs", "") or data.get("streaming_logs", "") or str(data)
                print(logs)
                print("-" * 60)
                return data
            else:
                print(f"❌ 获取失败: HTTP {response.status_code}")
                print(f"   响应: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ 出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_deployment_details(service_name: str):
    """获取部署详细信息"""
    if not API_KEY:
        print("❌ 未找到 API Key")
        return None
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE_URL}/v1/deployments/{service_name}"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取部署详情失败: HTTP {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ 出错: {str(e)}")
        return None

if __name__ == "__main__":
    service_name = "ai-job-assistant"
    
    print("=" * 60)
    print("📋 部署详细信息")
    print("=" * 60)
    print()
    
    # Get deployment details
    details = get_deployment_details(service_name)
    if details:
        print("📊 部署详情:")
        print(json.dumps(details, indent=2, ensure_ascii=False))
        print()
    
    print("=" * 60)
    print("📋 部署日志")
    print("=" * 60)
    print()
    
    # Get logs
    get_deployment_logs(service_name)
