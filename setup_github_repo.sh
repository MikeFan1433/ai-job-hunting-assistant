#!/bin/bash

# 设置 GitHub 仓库并推送代码
# 使用方法: ./setup_github_repo.sh [repository-name]

set -e

REPO_NAME=${1:-"ai-job-hunting-assistant"}
GITHUB_USER="MikeFan1433"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 设置 GitHub 仓库"
echo "===================="
echo ""
echo "📦 仓库名称: ${REPO_NAME}"
echo "👤 GitHub 用户: ${GITHUB_USER}"
echo "🔗 仓库 URL: ${REPO_URL}"
echo ""

# 检查 Git 状态
if [ ! -d ".git" ]; then
    echo "❌ 未找到 Git 仓库，正在初始化..."
    git init
    git add .
    git commit -m "Initial commit: AI Job Hunting Assistant"
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 发现未提交的更改，正在提交..."
    git add .
    git commit -m "Update: Prepare for GitHub deployment"
fi

# 检查远程仓库
if git remote | grep -q "^origin$"; then
    CURRENT_URL=$(git remote get-url origin)
    if [ "$CURRENT_URL" != "$REPO_URL" ]; then
        echo "⚠️  已存在远程仓库，但 URL 不同:"
        echo "   当前: ${CURRENT_URL}"
        echo "   目标: ${REPO_URL}"
        echo ""
        read -p "是否更新远程仓库 URL? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git remote set-url origin "$REPO_URL"
            echo "✅ 远程仓库 URL 已更新"
        else
            echo "⚠️  保持当前远程仓库 URL"
            REPO_URL="$CURRENT_URL"
        fi
    else
        echo "✅ 远程仓库已配置: ${REPO_URL}"
    fi
else
    echo "📡 添加远程仓库..."
    git remote add origin "$REPO_URL"
    echo "✅ 远程仓库已添加"
fi

# 设置主分支
echo ""
echo "🌿 设置主分支..."
git branch -M main 2>/dev/null || echo "已在 main 分支"

# 检查是否需要推送
echo ""
echo "📤 准备推送代码..."
echo ""

# 检查远程仓库是否存在
if git ls-remote --heads origin main &>/dev/null; then
    echo "✅ 远程仓库已存在"
    echo "📥 先拉取远程更改（如果有）..."
    git pull origin main --allow-unrelated-histories --no-edit || echo "⚠️  拉取失败，可能远程仓库为空或需要强制推送"
else
    echo "ℹ️  远程仓库不存在或为空"
    echo "   请确保在 GitHub 上已创建仓库: ${REPO_URL}"
    echo ""
    read -p "是否继续推送? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消推送"
        exit 1
    fi
fi

# 推送代码
echo ""
echo "🚀 推送代码到 GitHub..."
echo "   仓库: ${REPO_URL}"
echo "   分支: main"
echo ""

if git push -u origin main; then
    echo ""
    echo "✅ 代码推送成功！"
    echo ""
    echo "🔗 仓库链接: ${REPO_URL}"
    echo ""
    echo "📋 下一步:"
    echo "   1. 访问 ${REPO_URL} 确认代码已上传"
    echo "   2. 确保仓库是公开的（Public）"
    echo "   3. 运行部署脚本: python3 deploy_to_ai_builders.py"
    echo ""
    echo "💡 部署时需要的信息:"
    echo "   - GitHub URL: ${REPO_URL}"
    echo "   - Service Name: (例如: ai-job-assistant)"
    echo "   - Branch: main"
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "可能的原因:"
    echo "1. 远程仓库尚未在 GitHub 上创建"
    echo "2. 认证失败（需要配置 SSH key 或 Personal Access Token）"
    echo "3. 权限不足"
    echo ""
    echo "💡 解决方案:"
    echo "1. 访问 https://github.com/new 创建仓库: ${REPO_NAME}"
    echo "2. 确保仓库是公开的（Public）"
    echo "3. 配置 Git 认证（SSH key 或 Personal Access Token）"
    echo "4. 重新运行此脚本"
    exit 1
fi
