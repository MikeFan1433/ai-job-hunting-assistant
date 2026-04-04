# 服务启动指南

## 启动命令

### 后端服务
```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant"
python3 workflow_api.py
```

### 前端服务
```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant/frontend"
npm run dev
```

## 服务地址

- **后端 API**: http://localhost:8000
- **前端页面**: http://localhost:3000
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
打开浏览器访问: http://localhost:3000
