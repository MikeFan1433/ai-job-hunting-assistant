# 🚀 如何启动应用

## 方法 1: 使用启动脚本（推荐）

### 步骤 1: 启动后端 API

打开**第一个终端窗口**，运行：

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant"
./start_backend.sh
```

或者直接运行：

```bash
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000 --reload
```

**看到以下信息表示成功：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

**保持这个终端窗口打开！**

### 步骤 2: 启动前端

打开**第二个终端窗口**，运行：

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant/frontend"
npm run dev
```

**如果是第一次运行，需要先安装依赖：**

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant/frontend"
npm install
npm run dev
```

**看到以下信息表示成功：**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
```

### 步骤 3: 打开浏览器

在浏览器中访问：

```
http://localhost:3000
```

或者点击终端中显示的链接。

---

## 方法 2: 手动启动

### 启动后端

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant"
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000 --reload
```

### 启动前端

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant/frontend"
npm install  # 仅第一次需要
npm run dev
```

### 访问应用

打开浏览器访问：`http://localhost:3000`

---

## 📋 完整启动命令（复制粘贴）

### 终端 1 - 后端：

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant" && python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000 --reload
```

### 终端 2 - 前端：

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant/frontend" && npm install && npm run dev
```

---

## ✅ 检查是否成功

### 后端检查

在浏览器访问：`http://localhost:8000/api/v1/health`

应该看到：
```json
{"status":"healthy","timestamp":"..."}
```

### 前端检查

在浏览器访问：`http://localhost:3000`

应该看到输入页面（三个文本输入框）。

---

## 🐛 常见问题

### 问题 1: `npm: command not found`

**解决方案：** 需要安装 Node.js
- 访问 https://nodejs.org/ 下载安装
- 或使用 Homebrew: `brew install node`

### 问题 2: `python3: command not found`

**解决方案：** 
- macOS 通常自带 Python 3
- 如果没有，安装：`brew install python3`

### 问题 3: 端口被占用

**错误信息：** `Address already in use`

**解决方案：**
```bash
# 查找占用端口的进程
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 杀死进程（替换 PID 为实际进程号）
kill -9 PID
```

### 问题 4: 前端无法连接后端

**检查：**
1. 后端是否在运行？
2. 访问 `http://localhost:8000/api/v1/health` 是否有响应？
3. 查看浏览器控制台（F12）的错误信息

### 问题 5: 依赖安装失败

**解决方案：**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

---

## 📱 分享给朋友

如果想分享给朋友，运行：

```bash
./get_share_url.sh
```

会显示分享链接，例如：`http://192.168.1.183:3000`

---

## 🎯 快速参考

| 组件 | 端口 | 访问地址 |
|------|------|----------|
| 后端 API | 8000 | http://localhost:8000 |
| 前端应用 | 3000 | http://localhost:3000 |

---

## 💡 提示

- **两个终端都要保持打开**（一个后端，一个前端）
- 按 `Ctrl+C` 可以停止服务
- 修改代码后，前端会自动刷新
- 后端修改代码后会自动重启（--reload 模式）

---

## 🎉 开始使用

1. 启动后端和前端
2. 打开浏览器访问 `http://localhost:3000`
3. 输入 JD、Resume 和 Projects
4. 点击 "Start Analysis"
5. 等待处理完成
6. 查看结果和提供反馈

祝你使用愉快！🚀
