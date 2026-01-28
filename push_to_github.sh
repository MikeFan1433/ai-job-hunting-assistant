#!/bin/bash

# 推送代码到 GitHub 的辅助脚本
# 支持多种认证方式

set -e

REPO_NAME="ai-job-hunting-assistant"
GITHUB_USER="MikeFan1433"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📤 推送代码到 GitHub"
echo "===================="
echo ""
echo "📦 仓库: ${REPO_URL}"
echo ""

# 检查 Git 状态
if [ ! -d ".git" ]; then
    echo "❌ 未找到 Git 仓库"
    exit 1
fi

# 确保远程仓库配置正确
if git remote | grep -q "^origin$"; then
    git remote set-url origin "$REPO_URL"
else
    git remote add origin "$REPO_URL"
fi

echo "✅ 远程仓库已配置: ${REPO_URL}"
echo ""

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 发现未提交的更改，正在提交..."
    git add .
    git commit -m "Update: Prepare for GitHub push"
fi

# 设置主分支
git branch -M main 2>/dev/null || true

# 尝试不同的推送方式
echo "🚀 尝试推送代码..."
echo ""

# 方法 1: 尝试使用 GitHub CLI
if command -v gh &> /dev/null; then
    echo "📋 方法 1: 使用 GitHub CLI..."
    if gh auth status &>/dev/null; then
        echo "✅ GitHub CLI 已登录"
        if git push -u origin main; then
            echo ""
            echo "✅ 代码推送成功！"
            echo "🔗 仓库链接: ${REPO_URL}"
            exit 0
        fi
    else
        echo "⚠️  GitHub CLI 未登录"
        echo "   运行: gh auth login"
    fi
fi

# 方法 2: 尝试使用 SSH
echo ""
echo "📋 方法 2: 尝试使用 SSH..."
if ssh -T git@github.com &>/dev/null; then
    echo "✅ SSH 已配置"
    git remote set-url origin "git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
    if git push -u origin main; then
        echo ""
        echo "✅ 代码推送成功！"
        echo "🔗 仓库链接: ${REPO_URL}"
        exit 0
    fi
else
    echo "⚠️  SSH 未配置"
fi

# 方法 3: 提示用户手动操作
echo ""
echo "=" * 60
echo "⚠️  自动推送失败，需要配置认证"
echo "=" * 60
echo ""
echo "请选择以下方式之一:"
echo ""
echo "方式 1: 使用 GitHub CLI（推荐）"
echo "  1. 安装: brew install gh"
echo "  2. 登录: gh auth login"
echo "  3. 重新运行此脚本"
echo ""
echo "方式 2: 使用 Personal Access Token"
echo "  1. 访问: https://github.com/settings/tokens"
echo "  2. 创建 token (权限: repo)"
echo "  3. 运行:"
echo "     git remote set-url origin https://YOUR_TOKEN@github.com/${GITHUB_USER}/${REPO_NAME}.git"
echo "     git push -u origin main"
echo ""
echo "方式 3: 配置 SSH Key"
echo "  1. 生成 SSH key: ssh-keygen -t ed25519 -C 'your_email@example.com'"
echo "  2. 添加到 GitHub: https://github.com/settings/keys"
echo "  3. 重新运行此脚本"
echo ""
echo "方式 4: 在 GitHub 网页上创建仓库后手动推送"
echo "  1. 访问: https://github.com/new"
echo "  2. 创建仓库: ${REPO_NAME}"
echo "  3. 按照 GitHub 提供的推送命令操作"
echo ""
echo "💡 提示: 确保仓库是公开的（Public）"
echo ""

exit 1
