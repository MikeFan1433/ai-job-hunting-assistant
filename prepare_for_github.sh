#!/bin/bash

# 准备 GitHub 仓库的脚本
# 确保所有文件都适合上传到 GitHub

set -e

echo "📦 准备 GitHub 仓库"
echo "===================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查 .gitignore
if [ ! -f ".gitignore" ]; then
    echo "❌ .gitignore 不存在"
    exit 1
fi

echo "✅ .gitignore 已存在"

# 检查敏感文件是否会被提交
echo ""
echo "🔍 检查敏感文件..."
SENSITIVE_FILES=(".env" ".env.local" "*.key" "*.pem")

for pattern in "${SENSITIVE_FILES[@]}"; do
    if git ls-files "$pattern" 2>/dev/null | grep -q .; then
        echo "⚠️  警告: 发现敏感文件匹配 $pattern"
        echo "   这些文件应该被 .gitignore 排除"
    fi
done

# 检查是否有未提交的更改
echo ""
echo "📋 Git 状态:"
if git rev-parse --git-dir > /dev/null 2>&1; then
    git status --short | head -20
    echo ""
    
    UNCOMMITTED=$(git status --porcelain | wc -l | tr -d ' ')
    if [ "$UNCOMMITTED" -gt 0 ]; then
        echo "⚠️  有 $UNCOMMITTED 个未提交的更改"
        echo ""
        echo "建议提交这些更改:"
        echo "  git add ."
        echo "  git commit -m 'Prepare for GitHub and deployment'"
    else
        echo "✅ 所有更改已提交"
    fi
else
    echo "⚠️  尚未初始化 Git 仓库"
    echo "   运行: git init"
fi

# 检查是否有远程仓库
echo ""
echo "🔗 远程仓库:"
if git remote -v 2>/dev/null | grep -q .; then
    git remote -v
else
    echo "⚠️  尚未添加远程仓库"
    echo ""
    echo "在 GitHub 上创建仓库后，运行:"
    echo "  git remote add origin https://github.com/USERNAME/REPO_NAME.git"
    echo "  git branch -M main"
    echo "  git push -u origin main"
fi

echo ""
echo "=" * 60
echo "✅ 准备完成！"
echo ""
echo "下一步:"
echo "1. 在 GitHub 上创建公开仓库"
echo "2. 添加远程仓库并推送代码"
echo "3. 使用 deploy_to_ai_builders.py 执行部署"
