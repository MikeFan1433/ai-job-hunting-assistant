#!/bin/bash

# GitHub Repository 初始化脚本

set -e

echo "📦 准备 GitHub Repository"
echo "========================"
echo ""

# 检查是否已初始化 git
if [ ! -d ".git" ]; then
    echo "🔧 初始化 Git 仓库..."
    git init
    echo "✅ Git 仓库已初始化"
else
    echo "✅ Git 仓库已存在"
fi

echo ""
echo "📝 检查 .gitignore..."
if [ -f ".gitignore" ]; then
    echo "✅ .gitignore 已存在"
else
    echo "⚠️  .gitignore 不存在，请创建"
fi

echo ""
echo "📋 下一步操作:"
echo ""
echo "1. 在 GitHub 上创建新仓库:"
echo "   - 访问: https://github.com/new"
echo "   - 仓库名称: ai-job-hunting-assistant"
echo "   - 描述: AI-powered job hunting assistant with resume optimization"
echo "   - 选择: Public 或 Private"
echo "   - 不要初始化 README, .gitignore 或 license（我们已经有了）"
echo ""
echo "2. 添加远程仓库并推送:"
echo "   git add ."
echo "   git commit -m 'Initial commit: AI Job Hunting Assistant'"
echo "   git branch -M main"
echo "   git remote add origin https://github.com/YOUR_USERNAME/ai-job-hunting-assistant.git"
echo "   git push -u origin main"
echo ""
echo "3. 或者使用 SSH:"
echo "   git remote add origin git@github.com:YOUR_USERNAME/ai-job-hunting-assistant.git"
echo "   git push -u origin main"
echo ""
echo "✅ 准备完成！"
