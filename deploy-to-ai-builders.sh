#!/bin/bash

# 部署到 ai-builders.space 的专用脚本
# 使用方法: ./deploy-to-ai-builders.sh [your-app-name]

set -e

APP_NAME=${1:-"ai-job-assistant"}
DOMAIN="${APP_NAME}.ai-builders.space"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🚀 准备部署到 ai-builders.space"
echo "📦 应用名称: ${APP_NAME}"
echo "🌐 域名: ${DOMAIN}"
echo ""

cd "$SCRIPT_DIR"

# 步骤 1: 构建应用
echo "📦 步骤 1: 构建应用..."
if [ ! -f "build.sh" ]; then
    echo "❌ build.sh 不存在，请先创建构建脚本"
    exit 1
fi

chmod +x build.sh
./build.sh

# 步骤 2: 创建部署包
echo ""
echo "📦 步骤 2: 创建部署包..."
DEPLOY_PACKAGE="deployment-${APP_NAME}.tar.gz"

# 排除不必要的文件
tar -czf "${DEPLOY_PACKAGE}" \
  workflow_api.py \
  agent*.py \
  config.py \
  pdf_parser.py \
  resume_*.py \
  json_parser_utils.py \
  requirements.txt \
  build.sh \
  deploy.sh \
  frontend/dist/ \
  data/ \
  --exclude='data/vector_db/*' \
  --exclude='data/outputs/*' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='venv' \
  --exclude='node_modules' \
  --exclude='.git' \
  2>/dev/null || true

if [ ! -f "${DEPLOY_PACKAGE}" ]; then
    echo "❌ 创建部署包失败"
    exit 1
fi

echo "✅ 部署包已创建: ${DEPLOY_PACKAGE}"
echo ""

# 步骤 3: 显示部署信息
echo "📋 部署信息:"
echo "   - 部署包: ${DEPLOY_PACKAGE}"
echo "   - 域名: ${DOMAIN}"
echo "   - 大小: $(du -h ${DEPLOY_PACKAGE} | cut -f1)"
echo ""

# 步骤 4: 生成部署命令
echo "📝 下一步操作:"
echo ""
echo "1. 上传部署包到服务器:"
echo "   scp ${DEPLOY_PACKAGE} user@server.ai-builders.space:/path/to/apps/"
echo ""
echo "2. SSH 到服务器:"
echo "   ssh user@server.ai-builders.space"
echo ""
echo "3. 在服务器上执行以下命令:"
echo "   cd /path/to/apps/"
echo "   tar -xzf ${DEPLOY_PACKAGE}"
echo "   cd ${APP_NAME}/"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   pip install gunicorn"
echo "   export VITE_API_BASE_URL=https://${DOMAIN}"
echo "   ./deploy.sh"
echo ""
echo "4. 配置 Nginx (如果需要):"
echo "   参考 DEPLOYMENT.md 中的 Nginx 配置"
echo ""
echo "✅ 部署包已准备好！"
echo ""
