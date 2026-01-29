#!/bin/bash

# 一键更新脚本：同步到 GitHub 并重新部署到 ai-builders.space
# 使用方法: ./update_and_deploy.sh [commit-message]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 配置信息（从环境变量或默认值）
GITHUB_REPO_URL="${GITHUB_REPO_URL:-https://github.com/MikeFan1433/ai-job-hunting-assistant.git}"
SERVICE_NAME="${SERVICE_NAME:-ai-job-assistant}"
GIT_BRANCH="${GIT_BRANCH:-main}"
COMMIT_MSG="${1:-Update: $(date '+%Y-%m-%d %H:%M:%S')}"

echo "🔄 一键更新和部署脚本"
echo "===================="
echo ""
echo "📦 GitHub 仓库: ${GITHUB_REPO_URL}"
echo "🏷️  服务名称: ${SERVICE_NAME}"
echo "🌿 分支: ${GIT_BRANCH}"
echo ""

# 步骤 1: 检查 Git 状态
echo "📋 步骤 1: 检查更改..."
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ 没有未提交的更改"
    SKIP_COMMIT=true
else
    echo "📝 发现未提交的更改:"
    git status --short
    SKIP_COMMIT=false
fi
echo ""

# 步骤 2: 提交更改（如果有）
if [ "$SKIP_COMMIT" = false ]; then
    echo "📝 步骤 2: 提交更改..."
    git add .
    git commit -m "$COMMIT_MSG"
    echo "✅ 更改已提交: $COMMIT_MSG"
    echo ""
fi

# 步骤 3: 推送到 GitHub
echo "📤 步骤 3: 推送到 GitHub..."
if git push origin "$GIT_BRANCH"; then
    echo "✅ 代码已推送到 GitHub"
    echo ""
else
    echo "❌ 推送到 GitHub 失败"
    echo ""
    echo "可能的原因:"
    echo "1. 需要配置认证（SSH key 或 Personal Access Token）"
    echo "2. 网络连接问题"
    echo ""
    echo "💡 解决方案:"
    echo "   配置 SSH: git remote set-url origin git@github.com:MikeFan1433/ai-job-hunting-assistant.git"
    echo "   或使用 token: git remote set-url origin https://YOUR_TOKEN@github.com/MikeFan1433/ai-job-hunting-assistant.git"
    exit 1
fi

# 步骤 4: 询问是否重新部署
echo "🚀 步骤 4: 重新部署到 ai-builders.space"
echo ""
read -p "是否重新部署到 ai-builders.space? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📡 开始重新部署..."
    echo ""
    
    # 检查 Python 和部署脚本
    if [ ! -f "deploy_to_ai_builders.py" ]; then
        echo "❌ 未找到部署脚本: deploy_to_ai_builders.py"
        exit 1
    fi
    
    # 设置环境变量并运行部署脚本
    export GITHUB_REPO_URL="$GITHUB_REPO_URL"
    export SERVICE_NAME="$SERVICE_NAME"
    export GIT_BRANCH="$GIT_BRANCH"
    
    if python3 deploy_to_ai_builders.py; then
        echo ""
        echo "✅ 部署请求已提交"
        echo ""
        echo "⏳ 部署通常需要 5-10 分钟"
        echo "🔗 部署完成后访问: https://${SERVICE_NAME}.ai-builders.space"
        echo ""
        echo "💡 使用以下命令检查部署状态:"
        echo "   python3 check_deployment_status.py"
    else
        echo ""
        echo "❌ 部署失败"
        echo ""
        echo "请检查:"
        echo "1. API Key 是否正确配置（.env 文件）"
        echo "2. 服务名称是否正确"
        echo "3. GitHub 仓库是否为公开的"
        exit 1
    fi
else
    echo "⏭️  跳过部署"
    echo ""
    echo "💡 稍后可以手动运行部署:"
    echo "   python3 deploy_to_ai_builders.py"
fi

echo ""
echo "✅ 更新流程完成！"
echo ""
