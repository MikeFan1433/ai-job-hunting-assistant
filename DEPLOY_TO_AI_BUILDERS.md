# 🌐 部署到 ai-builders.space 完整指南

本指南将详细说明如何将 AI Job Hunting Assistant 部署到 `ai-builders.space` 域名。

## 📋 前置要求

1. **服务器访问权限**
   - 拥有 ai-builders.space 服务器的 SSH 访问权限
   - 知道服务器地址和登录凭据

2. **域名配置**
   - 确定你的应用名称（例如：`job-assistant`）
   - 完整域名将是：`job-assistant.ai-builders.space`

3. **环境准备**
   - 本地已安装 Python 3.8+ 和 Node.js 18+
   - 已配置 API 密钥（`.env` 文件）

## 🚀 快速部署（使用脚本）

### 步骤 1: 使用部署脚本

```bash
cd "AI Job Hunting Assistant"
chmod +x deploy-to-ai-builders.sh
./deploy-to-ai-builders.sh job-assistant
```

这将：
- 构建前端
- 创建部署包
- 显示部署指令

### 步骤 2: 上传到服务器

```bash
# 替换为实际的服务器信息
scp deployment-job-assistant.tar.gz user@server.ai-builders.space:/var/www/apps/
```

### 步骤 3: 在服务器上部署

```bash
# SSH 到服务器
ssh user@server.ai-builders.space

# 进入应用目录
cd /var/www/apps/

# 解压部署包
tar -xzf deployment-job-assistant.tar.gz

# 进入应用目录（如果解压到了子目录）
cd job-assistant/  # 或解压后的目录名

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 创建 .env 文件
cat > .env << EOF
STUDENT_PORTAL_BASE_URL=https://space.ai-builders.com/backend
STUDENT_PORTAL_API_KEY=your-api-key-here
VITE_API_BASE_URL=https://job-assistant.ai-builders.space
EOF

# 启动服务（测试）
./deploy.sh
```

## 📝 手动部署步骤

### 步骤 1: 本地构建

```bash
cd "AI Job Hunting Assistant"

# 构建前端
cd frontend
npm install
npm run build
cd ..

# 验证构建
ls -la frontend/dist/
```

### 步骤 2: 准备部署文件

创建部署包：

```bash
tar -czf deployment.tar.gz \
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
  --exclude='__pycache__'
```

### 步骤 3: 上传到服务器

```bash
# 方法 1: 使用 SCP
scp deployment.tar.gz user@server.ai-builders.space:/var/www/apps/

# 方法 2: 使用 SFTP
sftp user@server.ai-builders.space
put deployment.tar.gz /var/www/apps/
```

### 步骤 4: 服务器端设置

```bash
# SSH 到服务器
ssh user@server.ai-builders.space

# 创建应用目录
sudo mkdir -p /var/www/apps/job-assistant
cd /var/www/apps/job-assistant

# 解压文件
tar -xzf ../deployment.tar.gz

# 设置权限
sudo chown -R $USER:$USER /var/www/apps/job-assistant
```

### 步骤 5: 安装依赖

```bash
cd /var/www/apps/job-assistant

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
pip install gunicorn
```

### 步骤 6: 配置环境变量

```bash
# 创建 .env 文件
nano .env
```

添加以下内容：

```bash
# API 配置
STUDENT_PORTAL_BASE_URL=https://space.ai-builders.com/backend
STUDENT_PORTAL_API_KEY=your-actual-api-key-here

# LLM 配置
LLM_MODEL=supermind-agent-v1
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4000

# 前端 API URL
VITE_API_BASE_URL=https://job-assistant.ai-builders.space
```

保存并退出（Ctrl+X, Y, Enter）

### 步骤 7: 配置 systemd 服务

创建 systemd 服务文件：

```bash
sudo nano /etc/systemd/system/ai-job-assistant.service
```

添加以下内容：

```ini
[Unit]
Description=AI Job Hunting Assistant
After=network.target

[Service]
Type=simple
User=your-username
Group=your-group
WorkingDirectory=/var/www/apps/job-assistant
Environment="PATH=/var/www/apps/job-assistant/venv/bin"
EnvironmentFile=/var/www/apps/job-assistant/.env
ExecStart=/var/www/apps/job-assistant/venv/bin/gunicorn workflow_api:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 300 \
    --access-logfile /var/log/ai-job-assistant/access.log \
    --error-logfile /var/log/ai-job-assistant/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

创建日志目录：

```bash
sudo mkdir -p /var/log/ai-job-assistant
sudo chown your-username:your-group /var/log/ai-job-assistant
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-job-assistant
sudo systemctl start ai-job-assistant
sudo systemctl status ai-job-assistant
```

### 步骤 8: 配置 Nginx

创建 Nginx 配置文件：

```bash
sudo nano /etc/nginx/sites-available/job-assistant.ai-builders.space
```

添加以下内容：

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name job-assistant.ai-builders.space;
    
    return 301 https://$server_name$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name job-assistant.ai-builders.space;

    # SSL 证书（使用 Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/job-assistant.ai-builders.space/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/job-assistant.ai-builders.space/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/job-assistant-access.log;
    error_log /var/log/nginx/job-assistant-error.log;

    # 代理到后端
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 静态文件缓存
    location /assets/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/job-assistant.ai-builders.space /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 步骤 9: 配置 SSL 证书

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d job-assistant.ai-builders.space

# 测试自动续期
sudo certbot renew --dry-run
```

### 步骤 10: 配置 DNS

在域名管理面板中添加 A 记录：

```
类型: A
名称: job-assistant (或 @)
值: 服务器IP地址
TTL: 3600
```

## ✅ 验证部署

### 1. 检查服务状态

```bash
# 检查 systemd 服务
sudo systemctl status ai-job-assistant

# 检查 Nginx
sudo systemctl status nginx

# 检查端口
sudo netstat -tlnp | grep 8000
```

### 2. 测试 API

```bash
# 健康检查
curl https://job-assistant.ai-builders.space/api/v1/health

# 应该返回:
# {"status":"healthy","timestamp":"..."}
```

### 3. 测试前端

在浏览器中访问：
```
https://job-assistant.ai-builders.space
```

### 4. 测试完整功能

- 输入 JD 和简历
- 提交表单
- 检查工作流是否正常运行
- 查看日志确认没有错误

## 🔧 维护和更新

### 更新应用

```bash
# 1. 在本地构建新版本
./build.sh

# 2. 创建新的部署包
./deploy-to-ai-builders.sh job-assistant

# 3. 上传到服务器
scp deployment-job-assistant.tar.gz user@server.ai-builders.space:/tmp/

# 4. 在服务器上更新
ssh user@server.ai-builders.space
cd /var/www/apps/job-assistant
sudo systemctl stop ai-job-assistant
tar -xzf /tmp/deployment-job-assistant.tar.gz
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start ai-job-assistant
```

### 查看日志

```bash
# 应用日志
sudo journalctl -u ai-job-assistant -f

# Nginx 日志
sudo tail -f /var/log/nginx/job-assistant-access.log
sudo tail -f /var/log/nginx/job-assistant-error.log

# 应用错误日志
sudo tail -f /var/log/ai-job-assistant/error.log
```

### 重启服务

```bash
sudo systemctl restart ai-job-assistant
sudo systemctl reload nginx
```

## 🐛 故障排除

### 问题 1: 服务无法启动

```bash
# 检查日志
sudo journalctl -u ai-job-assistant -n 50

# 检查 Python 环境
cd /var/www/apps/job-assistant
source venv/bin/activate
python -c "import workflow_api"
```

### 问题 2: 502 Bad Gateway

- 检查后端服务是否运行：`sudo systemctl status ai-job-assistant`
- 检查端口 8000 是否监听：`sudo netstat -tlnp | grep 8000`
- 检查 Nginx 配置：`sudo nginx -t`

### 问题 3: 前端显示空白

- 检查 `frontend/dist/` 是否存在
- 检查浏览器控制台错误
- 检查 API 基础 URL 配置

### 问题 4: SSL 证书问题

```bash
# 检查证书
sudo certbot certificates

# 手动续期
sudo certbot renew
```

## 📊 性能优化

### 1. 增加 Worker 数量

编辑 systemd 服务文件，增加 workers：

```ini
ExecStart=... --workers 8 ...
```

### 2. 启用 Gzip 压缩

在 Nginx 配置中添加：

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

### 3. 静态文件缓存

已在 Nginx 配置中包含静态文件缓存。

## 🔒 安全建议

1. **限制 CORS**：更新 `workflow_api.py` 中的 CORS 配置
2. **防火墙**：只开放必要端口（80, 443）
3. **定期更新**：保持系统和依赖更新
4. **备份**：定期备份 `data/` 目录
5. **监控**：设置监控和告警

## 📚 相关文档

- `DEPLOYMENT.md` - 通用部署指南
- `QUICK_DEPLOY.md` - 快速部署指南
- `build.sh` - 构建脚本
- `deploy.sh` - 部署脚本

## 🆘 需要帮助？

如果遇到问题：
1. 检查服务器日志
2. 验证环境变量配置
3. 测试 API 端点
4. 检查 DNS 和 SSL 配置

---

**部署完成后，你的应用将在 `https://job-assistant.ai-builders.space` 可用！** 🎉
