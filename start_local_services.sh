#!/bin/bash

# 启动本地开发服务的脚本
# 确保后端和前端服务长期运行

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 启动本地开发服务..."
echo ""

# 检查并启动后端
if ! lsof -ti:8000 >/dev/null 2>&1; then
    echo "📦 启动后端服务 (端口 8000)..."
    nohup python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
    sleep 3
    if lsof -ti:8000 >/dev/null 2>&1; then
        echo "✅ 后端服务已启动"
    else
        echo "❌ 后端服务启动失败，请检查日志: /tmp/backend.log"
    fi
else
    echo "✅ 后端服务已在运行"
fi

# 检查并启动前端
FRONTEND_PORT=""
for port in 3000 3001 5173; do
    if lsof -ti:$port >/dev/null 2>&1; then
        FRONTEND_PORT=$port
        break
    fi
done

if [ -z "$FRONTEND_PORT" ]; then
    echo "📦 启动前端服务..."
    cd frontend
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    cd ..
    sleep 5
    
    # 检查前端启动的端口
    for port in 3000 3001 5173; do
        if lsof -ti:$port >/dev/null 2>&1; then
            FRONTEND_PORT=$port
            break
        fi
    done
    
    if [ -n "$FRONTEND_PORT" ]; then
        echo "✅ 前端服务已启动 (端口 $FRONTEND_PORT)"
    else
        echo "⏳ 前端服务正在启动中..."
    fi
else
    echo "✅ 前端服务已在运行 (端口 $FRONTEND_PORT)"
fi

echo ""
echo "🎉 服务启动完成！"
echo ""
echo "📱 访问链接:"
if [ -n "$FRONTEND_PORT" ]; then
    echo "   👉 http://localhost:$FRONTEND_PORT"
else
    echo "   ⏳ 前端服务正在启动，请稍候..."
    echo "   💡 稍后访问: http://localhost:3000 或 http://localhost:3001"
fi
echo ""
echo "📝 日志文件:"
echo "   - 后端: /tmp/backend.log"
echo "   - 前端: /tmp/frontend.log"
echo ""
echo "🛑 停止服务:"
echo "   - 后端: lsof -ti:8000 | xargs kill"
echo "   - 前端: lsof -ti:3000,3001,5173 | xargs kill"
echo ""
