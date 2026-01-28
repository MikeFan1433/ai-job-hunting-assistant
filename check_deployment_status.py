#!/usr/bin/env python3
"""
检查 AI Builders 部署状态
根据部署指南，通过 API 查询部署状态
"""

import os
import sys
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = os.getenv(
    "STUDENT_PORTAL_BASE_URL",
    "https://space.ai-builders.com/backend"
)

# Get API key
API_KEY = (
    os.getenv("STUDENT_PORTAL_API_KEY") or
    os.getenv("AI_BUILDER_TOKEN") or
    os.getenv("AI_BUILDER_API_TOKEN") or
    os.getenv("SUPER_MIND_API_KEY") or
    os.getenv("OPENAI_API_KEY")
)

def check_deployment_status(service_name: str):
    """检查部署状态"""
    if not API_KEY:
        print("❌ 未找到 API Key")
        print("   请设置以下环境变量之一:")
        print("   - STUDENT_PORTAL_API_KEY")
        print("   - AI_BUILDER_TOKEN")
        print("   - AI_BUILDER_API_TOKEN")
        return None
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Get deployment status
    # According to deployment guide, use GET /v1/deployments/{service_name}
    url = f"{API_BASE_URL}/v1/deployments/{service_name}"
    
    try:
        print(f"🔍 检查部署状态: {service_name}")
        print(f"📡 API URL: {url}")
        print()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 部署状态查询成功")
                print()
                print("📊 部署信息:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return data
            elif response.status_code == 404:
                print(f"⚠️  服务 '{service_name}' 未找到")
                print("   可能尚未部署，或服务名称不正确")
                return None
            else:
                print(f"❌ 查询失败: HTTP {response.status_code}")
                print(f"   响应: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ 查询出错: {str(e)}")
        return None

def list_all_deployments():
    """列出所有部署"""
    if not API_KEY:
        print("❌ 未找到 API Key")
        return None
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # List all deployments
    # According to deployment guide, use GET /v1/deployments
    url = f"{API_BASE_URL}/v1/deployments"
    
    try:
        print("🔍 查询所有部署...")
        print(f"📡 API URL: {url}")
        print()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 查询成功")
                print()
                
                deployments = data.get("deployments", []) if isinstance(data, dict) else data
                
                if deployments:
                    print(f"📋 找到 {len(deployments)} 个部署:")
                    print()
                    for i, deployment in enumerate(deployments, 1):
                        service_name = deployment.get("service_name", "unknown")
                        status = deployment.get("status", "unknown")
                        url = deployment.get("url", "N/A")
                        
                        print(f"{i}. 服务名称: {service_name}")
                        print(f"   状态: {status}")
                        print(f"   URL: {url}")
                        print()
                else:
                    print("⚠️  没有找到任何部署")
                
                return deployments
            else:
                print(f"❌ 查询失败: HTTP {response.status_code}")
                print(f"   响应: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ 查询出错: {str(e)}")
        return None

def main():
    print("=" * 60)
    print("🔍 AI Builders 部署状态检查")
    print("=" * 60)
    print()
    
    # First, try to list all deployments
    print("📋 步骤 1: 查询所有部署")
    print("-" * 60)
    deployments = list_all_deployments()
    
    print()
    print("=" * 60)
    
    if deployments:
        print("✅ 找到部署记录")
        print()
        print("💡 提示:")
        print("   - 如果状态是 'running' 或 'active'，说明部署成功")
        print("   - 如果状态是 'deploying'，请等待 5-10 分钟")
        print("   - 如果状态是 'failed'，请检查日志")
        print()
        print("🔗 访问链接:")
        for deployment in deployments:
            url = deployment.get("url", "")
            if url:
                print(f"   - {url}")
    else:
        print("⚠️  未找到部署记录")
        print()
        print("可能的原因:")
        print("1. 尚未执行部署")
        print("2. 服务名称不正确")
        print("3. API Key 配置错误")
        print()
        print("💡 如果需要部署，请提供:")
        print("   - GitHub Repository URL")
        print("   - Service Name")
        print("   - Git Branch")
    
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
