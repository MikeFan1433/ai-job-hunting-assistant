#!/bin/bash
# Node.js 安装助手脚本

echo "📦 Node.js 安装助手"
echo "===================="
echo ""

# 检查是否已安装
if command -v node &> /dev/null; then
    echo "✅ Node.js 已安装: $(node --version)"
    echo "✅ npm 已安装: $(npm --version)"
    exit 0
fi

echo "❌ Node.js 未安装"
echo ""
echo "请选择安装方法:"
echo ""
echo "1. 使用官方安装包（推荐）"
echo "   - 访问: https://nodejs.org/"
echo "   - 下载并安装 LTS 版本"
echo ""
echo "2. 使用 Homebrew"
echo "   - 运行: brew install node"
echo ""
echo "3. 使用 nvm"
echo "   - 运行: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
echo "   - 然后: nvm install --lts"
echo ""
echo "安装完成后，运行以下命令验证:"
echo "  node --version"
echo "  npm --version"
echo ""
echo "然后运行构建脚本:"
echo "  ./build.sh"
echo ""

# 尝试检测 Homebrew
if command -v brew &> /dev/null; then
    echo "检测到 Homebrew，是否使用 Homebrew 安装？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "正在安装 Node.js..."
        brew install node
        if command -v node &> /dev/null; then
            echo "✅ 安装成功！"
            echo "Node.js: $(node --version)"
            echo "npm: $(npm --version)"
        else
            echo "❌ 安装失败，请手动安装"
        fi
    fi
else
    echo "💡 提示: 安装 Homebrew 可以更方便地管理软件"
    echo "   安装命令: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
fi
