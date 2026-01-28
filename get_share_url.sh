#!/bin/bash

# Get shareable URL for the application

echo "🌐 获取分享链接"
echo ""

# Get IP address
IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

if [ -z "$IP" ]; then
    IP=$(ipconfig getifaddr en0 2>/dev/null)
fi

if [ -z "$IP" ]; then
    echo "❌ 无法获取 IP 地址"
    echo "请手动运行: ifconfig | grep 'inet '"
    exit 1
fi

echo "✅ 你的 IP 地址: $IP"
echo ""
echo "📱 分享链接:"
echo "   http://$IP:3000"
echo ""
echo "💡 使用方法:"
echo "   1. 确保后端和前端都在运行"
echo "   2. 确保朋友和你在同一个 WiFi 网络"
echo "   3. 把上面的链接分享给朋友"
echo ""
