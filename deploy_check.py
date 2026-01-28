#!/usr/bin/env python3
"""
部署前检查脚本 - 验证部署准备状态
"""

import os
import sys
from pathlib import Path

def check_dockerfile():
    """检查 Dockerfile 是否符合要求"""
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        return False, "Dockerfile 不存在"
    
    content = dockerfile_path.read_text()
    
    # 检查是否使用 shell form (sh -c)
    if 'sh -c' not in content or '${PORT:-8000}' not in content:
        return False, "Dockerfile CMD 必须使用 shell form (sh -c) 并支持 PORT 环境变量"
    
    # 检查是否暴露端口
    if 'EXPOSE' not in content:
        return False, "Dockerfile 必须包含 EXPOSE 指令"
    
    return True, "Dockerfile 配置正确"

def check_frontend_build():
    """检查前端是否已构建"""
    dist_path = Path("frontend/dist")
    if not dist_path.exists():
        return False, "前端未构建，请运行 ./build.sh"
    
    index_html = dist_path / "index.html"
    if not index_html.exists():
        return False, "frontend/dist/index.html 不存在"
    
    return True, "前端构建文件存在"

def check_static_serving():
    """检查后端是否配置了静态文件服务"""
    api_file = Path("workflow_api.py")
    if not api_file.exists():
        return False, "workflow_api.py 不存在"
    
    content = api_file.read_text()
    
    # 检查是否配置了静态文件服务
    if 'frontend_dist_dir' not in content or 'StaticFiles' not in content:
        return False, "后端未配置前端静态文件服务"
    
    return True, "静态文件服务已配置"

def check_gitignore():
    """检查 .gitignore 是否排除了敏感文件"""
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        return False, ".gitignore 不存在"
    
    content = gitignore_path.read_text()
    
    if '.env' not in content:
        return False, ".gitignore 未排除 .env 文件"
    
    return True, ".gitignore 配置正确"

def main():
    print("🔍 部署准备检查")
    print("=" * 60)
    print()
    
    checks = [
        ("Dockerfile", check_dockerfile),
        ("前端构建", check_frontend_build),
        ("静态文件服务", check_static_serving),
        (".gitignore", check_gitignore),
    ]
    
    all_passed = True
    for name, check_func in checks:
        passed, message = check_func()
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {message}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("🎉 所有检查通过！仓库已准备好部署。")
        print()
        print("下一步:")
        print("1. 确保所有更改已提交并推送到 GitHub")
        print("2. 准备以下信息进行部署:")
        print("   - GitHub 仓库 URL (必须是公开的)")
        print("   - Service Name (将成为子域名)")
        print("   - Git Branch (例如: main)")
        return 0
    else:
        print("⚠️  发现一些问题，请先修复后再部署。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
