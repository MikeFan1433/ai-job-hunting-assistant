# 📦 安装 Node.js 指南

## 方法 1: 使用官方安装包（推荐，最简单）

### macOS

1. **访问 Node.js 官网**
   - 打开：https://nodejs.org/
   - 下载 LTS 版本（推荐）

2. **安装**
   - 双击下载的 `.pkg` 文件
   - 按照安装向导完成安装

3. **验证安装**
   ```bash
   node --version
   npm --version
   ```

## 方法 2: 使用 Homebrew

### 安装 Homebrew（如果还没有）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 安装 Node.js

```bash
brew install node
```

### 验证安装

```bash
node --version
npm --version
```

## 方法 3: 使用 nvm (Node Version Manager)

### 安装 nvm

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
```

### 重新加载 shell 配置

```bash
source ~/.zshrc  # 或 ~/.bash_profile
```

### 安装 Node.js

```bash
nvm install --lts
nvm use --lts
```

### 验证安装

```bash
node --version
npm --version
```

## ✅ 安装后验证

运行以下命令验证安装：

```bash
node --version   # 应该显示版本号，如 v20.11.0
npm --version    # 应该显示版本号，如 10.2.4
```

## 🚀 安装完成后

安装 Node.js 后，运行：

```bash
cd "AI Job Hunting Assistant"
./build.sh
```

这将：
1. 安装前端依赖
2. 构建前端应用
3. 准备部署文件

## 📝 快速检查

运行测试脚本检查环境：

```bash
python3 test_deployment.py
```

## 🆘 遇到问题？

### 问题 1: 命令未找到

如果安装后仍然显示 `command not found`：

1. **重新打开终端**
2. **检查 PATH 环境变量**
   ```bash
   echo $PATH
   ```
3. **手动添加到 PATH**（如果需要）
   ```bash
   export PATH="/usr/local/bin:$PATH"
   ```

### 问题 2: 权限问题

如果遇到权限错误：

```bash
sudo chown -R $(whoami) ~/.npm
```

### 问题 3: 版本问题

确保安装的是 LTS 版本（长期支持版本），推荐 Node.js 18 或更高版本。

## 📚 更多信息

- Node.js 官网: https://nodejs.org/
- npm 文档: https://docs.npmjs.com/
- nvm 文档: https://github.com/nvm-sh/nvm
