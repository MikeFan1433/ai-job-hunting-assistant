# 服务启动指南

以下命令均在 **`AI Job Hunting Assistant` 目录**（本文件所在目录）下执行，无需写死本机绝对路径。

## 启动命令

### 后端服务
```bash
python3 workflow_api.py
```

### 前端服务
```bash
cd frontend
npm run dev
```

## 服务地址

- **后端 API**: http://localhost:8000
- **前端页面**: http://localhost:3000（若 `vite` 使用其他端口，以终端输出为准）
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

## 环境变量

确保设置：
```bash
export AI_BUILDER_TOKEN=<your_token>
```

或在 `.env` 文件中：
```
AI_BUILDER_TOKEN=<your_token>
```

## 验证服务

### 检查后端
```bash
curl http://localhost:8000/api/v1/health
```

### 检查前端
在浏览器中打开前端 dev 服务器提示的本地 URL（常见为 `http://localhost:5173` 或 `http://localhost:3000`）。
