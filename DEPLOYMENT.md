# 🚀 部署指南 - AI Job Hunting Assistant

本指南将帮助你将应用部署到公共域名，让所有人都可以使用。

## 📋 部署前准备

### 1. 环境要求

- Python 3.8+
- Node.js 18+
- npm 或 yarn

### 2. 构建应用

运行构建脚本：

```bash
cd "AI Job Hunting Assistant"
chmod +x build.sh deploy.sh
./build.sh
```

这将：
- 安装前端依赖
- 构建前端（生成 `frontend/dist/`）
- 检查后端依赖

## 🌐 部署选项

### 选项 1: 部署到 ai-builders.space（推荐）

如果你有 ai-builders.space 的访问权限，可以按照以下步骤部署：

#### 步骤 1: 准备部署文件

```bash
# 构建应用
./build.sh

# 创建部署包
tar -czf deployment.tar.gz \
  workflow_api.py \
  agent*.py \
  config.py \
  pdf_parser.py \
  resume_*.py \
  json_parser_utils.py \
  requirements.txt \
  frontend/dist/ \
  data/ \
  --exclude='data/vector_db/*' \
  --exclude='data/outputs/*'
```

#### 步骤 2: 上传到服务器

```bash
# 使用 scp 上传（替换为实际服务器地址）
scp deployment.tar.gz user@your-server.ai-builders.space:/path/to/app/

# SSH 到服务器
ssh user@your-server.ai-builders.space

# 解压
cd /path/to/app/
tar -xzf deployment.tar.gz

# 设置环境变量
export VITE_API_BASE_URL=https://your-app.ai-builders.space
```

#### 步骤 3: 在服务器上运行

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 gunicorn（推荐用于生产）
pip install gunicorn

# 启动服务
./deploy.sh
```

#### 步骤 4: 使用进程管理器（PM2 或 systemd）

**使用 systemd（推荐）：**

创建 `/etc/systemd/system/ai-job-assistant.service`:

```ini
[Unit]
Description=AI Job Hunting Assistant
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/app
Environment="PATH=/path/to/app/venv/bin"
ExecStart=/path/to/app/venv/bin/gunicorn workflow_api:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable ai-job-assistant
sudo systemctl start ai-job-assistant
sudo systemctl status ai-job-assistant
```

### 选项 2: 部署到 Vercel + Railway

#### 前端部署到 Vercel

```bash
cd frontend
npm install -g vercel
vercel
```

在 Vercel 中设置环境变量：
- `VITE_API_BASE_URL`: 你的后端 API 地址

#### 后端部署到 Railway

1. 访问 [Railway](https://railway.app)
2. 创建新项目
3. 连接 GitHub 仓库或上传代码
4. 设置启动命令：`gunicorn workflow_api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. 设置环境变量

### 选项 3: 部署到 Render

#### 前端部署

1. 访问 [Render](https://render.com)
2. 创建新的 Static Site
3. 连接 GitHub 仓库
4. 构建命令：`cd frontend && npm install && npm run build`
5. 发布目录：`frontend/dist`

#### 后端部署

1. 创建新的 Web Service
2. 构建命令：`pip install -r requirements.txt`
3. 启动命令：`gunicorn workflow_api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
4. 设置环境变量

### 选项 4: Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application
COPY . .

# Build frontend (if not already built)
WORKDIR /app/frontend
RUN if [ ! -d "node_modules" ]; then \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install && \
    npm run build; \
    fi

WORKDIR /app

# Expose port
EXPOSE 8000

# Start server
CMD ["gunicorn", "workflow_api:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

部署：

```bash
docker-compose up -d
```

## 🔧 环境变量配置

创建 `.env` 文件（不要提交到 Git）：

```bash
# API Configuration
STUDENT_PORTAL_BASE_URL=https://space.ai-builders.com/backend
STUDENT_PORTAL_API_KEY=your-api-key-here

# LLM Configuration
LLM_MODEL=supermind-agent-v1
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4000

# Frontend API URL (for production)
VITE_API_BASE_URL=https://your-app.ai-builders.space
```

## 🔒 安全配置

### 1. CORS 配置

在生产环境中，更新 `workflow_api.py` 中的 CORS 设置：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.ai-builders.space",
        "https://your-frontend-domain.com"
    ],  # 限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. API 密钥保护

确保 `.env` 文件不被提交到 Git。添加到 `.gitignore`:

```
.env
.env.local
*.pyc
__pycache__/
venv/
node_modules/
frontend/dist/
```

## 📊 监控和日志

### 使用 PM2（Node.js 进程管理器）

```bash
npm install -g pm2
pm2 start deploy.sh --name ai-job-assistant
pm2 save
pm2 startup
```

### 查看日志

```bash
# systemd
sudo journalctl -u ai-job-assistant -f

# PM2
pm2 logs ai-job-assistant

# Docker
docker-compose logs -f
```

## 🧪 测试部署

### 1. 健康检查

```bash
curl https://your-app.ai-builders.space/api/v1/health
```

应该返回：
```json
{"status":"healthy","timestamp":"..."}
```

### 2. 前端访问

在浏览器中打开：
```
https://your-app.ai-builders.space
```

### 3. API 测试

```bash
curl -X POST https://your-app.ai-builders.space/api/v1/workflow/start \
  -H "Content-Type: application/json" \
  -d '{"jd_text":"test","resume_text":"test"}'
```

## 🐛 常见问题

### 问题 1: 前端无法加载

**解决方案：**
- 检查 `frontend/dist/` 目录是否存在
- 检查后端是否正确配置了静态文件服务
- 检查浏览器控制台的错误信息

### 问题 2: API 调用失败

**解决方案：**
- 检查 `VITE_API_BASE_URL` 环境变量
- 检查 CORS 配置
- 检查后端日志

### 问题 3: 静态资源 404

**解决方案：**
- 确保运行了 `./build.sh`
- 检查 `frontend/dist/assets/` 目录
- 检查后端路由配置

## 📝 部署清单

- [ ] 运行 `./build.sh` 构建前端
- [ ] 配置环境变量
- [ ] 更新 CORS 设置
- [ ] 测试本地部署
- [ ] 上传到服务器
- [ ] 配置进程管理器
- [ ] 设置 SSL 证书（HTTPS）
- [ ] 配置域名 DNS
- [ ] 测试生产环境
- [ ] 设置监控和日志

## 🔗 相关文件

- `build.sh` - 构建脚本
- `deploy.sh` - 部署脚本
- `workflow_api.py` - 后端 API
- `frontend/vite.config.ts` - 前端构建配置
- `frontend/src/services/api.ts` - API 客户端配置

## 💡 提示

1. **使用 HTTPS**：生产环境必须使用 HTTPS
2. **设置反向代理**：使用 Nginx 或 Caddy 作为反向代理
3. **监控资源使用**：定期检查 CPU 和内存使用情况
4. **备份数据**：定期备份 `data/` 目录
5. **更新依赖**：定期更新 Python 和 Node.js 依赖

## 🆘 需要帮助？

如果遇到问题，请检查：
1. 服务器日志
2. 浏览器控制台
3. 网络连接
4. 环境变量配置
