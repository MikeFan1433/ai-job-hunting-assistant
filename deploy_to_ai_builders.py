#!/usr/bin/env python3
"""
部署到 AI Builders 平台
根据 deployment-prompt.md 的指南执行部署
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

def deploy_to_ai_builders(repo_url: str, service_name: str, branch: str = "main", env_vars: dict = None):
    """
    部署应用到 AI Builders 平台
    
    Args:
        repo_url: GitHub 仓库 URL (必须是公开的)
        service_name: 服务名称 (将成为子域名)
        branch: Git 分支名称
        env_vars: 额外的环境变量 (可选)
    """
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
    
    # Prepare deployment request
    # According to deployment guide: POST /v1/deployments
    url = f"{API_BASE_URL}/v1/deployments"
    
    payload = {
        "repo_url": repo_url,
        "service_name": service_name,
        "branch": branch
    }
    
    # Add environment variables if provided
    if env_vars:
        payload["env_vars"] = env_vars
    
    try:
        print("🚀 开始部署到 AI Builders...")
        print("=" * 60)
        print(f"📦 仓库: {repo_url}")
        print(f"🏷️  服务名称: {service_name}")
        print(f"🌿 分支: {branch}")
        print(f"🌐 部署后 URL: https://{service_name}.ai-builders.space")
        print()
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                print("✅ 部署请求已提交")
                print()
                print("📊 部署信息:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print()
                
                # Check for streaming logs
                streaming_logs = data.get("streaming_logs", "")
                if streaming_logs:
                    print("📋 构建日志:")
                    print("-" * 60)
                    print(streaming_logs)
                    print("-" * 60)
                else:
                    print("ℹ️  构建日志将在部署过程中生成")
                    print("   可以使用 GET /v1/deployments/{service_name}/logs 查看完整日志")
                
                print()
                print("⏳ 部署通常需要 5-10 分钟")
                print(f"🔗 部署完成后访问: https://{service_name}.ai-builders.space")
                print()
                print("💡 提示:")
                print("   - 使用 check_deployment_status.py 检查部署状态")
                print("   - 或访问 Deployment Portal 查看进度")
                
                return data
            else:
                print(f"❌ 部署失败: HTTP {response.status_code}")
                print(f"   响应: {response.text}")
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        print(f"   错误详情: {error_data['detail']}")
                except:
                    pass
                return None
                
    except Exception as e:
        print(f"❌ 部署出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 60)
    print("🚀 AI Builders 部署工具")
    print("=" * 60)
    print()
    
    # Check if API key is available
    if not API_KEY:
        print("❌ 未找到 API Key")
        print()
        print("请设置以下环境变量之一:")
        print("   - STUDENT_PORTAL_API_KEY")
        print("   - AI_BUILDER_TOKEN")
        print("   - AI_BUILDER_API_TOKEN")
        print()
        print("或在 .env 文件中设置:")
        print("   AI_BUILDER_TOKEN=your-token-here")
        return 1
    
    # Get deployment info from user or environment
    repo_url = os.getenv("GITHUB_REPO_URL")
    service_name = os.getenv("SERVICE_NAME")
    branch = os.getenv("GIT_BRANCH", "main")
    
    if not repo_url or not service_name:
        print("📋 需要以下信息进行部署:")
        print()
        
        if not repo_url:
            repo_url = input("1. GitHub 仓库 URL (必须是公开的): ").strip()
        
        if not service_name:
            service_name = input("2. Service Name (将成为子域名): ").strip()
        
        branch_input = input(f"3. Git Branch (默认: {branch}): ").strip()
        if branch_input:
            branch = branch_input
    
    if not repo_url or not service_name:
        print("❌ 缺少必要信息，部署取消")
        return 1
    
    # Validate inputs
    if not repo_url.startswith("https://github.com/"):
        print("❌ GitHub 仓库 URL 格式不正确")
        print("   应该是: https://github.com/username/repo-name")
        return 1
    
    if not service_name.replace("-", "").replace("_", "").isalnum():
        print("❌ Service Name 只能包含字母、数字、连字符和下划线")
        return 1
    
    print()
    print("=" * 60)
    
    # Deploy
    result = deploy_to_ai_builders(repo_url, service_name, branch)
    
    if result:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
