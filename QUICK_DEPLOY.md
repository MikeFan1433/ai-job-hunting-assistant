# 🚀 快速部署指南

## 三步部署到公共域名

### 步骤 1: 构建应用

```bash
cd "AI Job Hunting Assistant"
./build.sh
```

这将构建前端并准备所有文件。

### 步骤 2: 测试本地部署

```bash
./deploy.sh
```

然后在浏览器中访问 `http://localhost:8000` 测试。

### 步骤 3: 部署到服务器

#### 选项 A: 部署到 ai-builders.space

1. **准备部署包**：
```bash
# 构建应用
./build.sh

# 创建部署包（排除不必要的文件）
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

2. **上传到服务器**：
```bash
scp deployment.tar.gz user@server.ai-builders.space:/path/to/app/
```

3. **在服务器上部署**：
```bash
# SSH 到服务器
ssh user@server.ai-builders.space

# 解压
cd /path/to/app/
tar -xzf deployment.tar.gz

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 设置环境变量
export VITE_API_BASE_URL=https://your-app.ai-builders.space

# 启动服务
./deploy.sh
```

#### 选项 B: 使用 Docker

```bash
# 构建 Docker 镜像
docker build -t ai-job-assistant .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e VITE_API_BASE_URL=https://your-app.ai-builders.space \
  --name ai-job-assistant \
  ai-job-assistant
```

#### 选项 C: 使用 Render/Railway/Vercel

详细说明请查看 `DEPLOYMENT.md`。

## 🔧 配置域名

### 1. 设置 DNS

将你的域名指向服务器 IP：
```
A 记录: your-app.ai-builders.space -> 服务器IP
```

### 2. 配置 Nginx（推荐）

创建 `/etc/nginx/sites-available/ai-job-assistant`:

```nginx
server {
    listen 80;
    server_name your-app.ai-builders.space;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-app.ai-builders.space;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/ai-job-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. 使用 Let's Encrypt SSL

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-app.ai-builders.space
```

## ✅ 验证部署

1. **健康检查**：
```bash
curl https://your-app.ai-builders.space/api/v1/health
```

2. **访问应用**：
在浏览器中打开 `https://your-app.ai-builders.space`

3. **测试功能**：
- 输入 JD 和简历
- 提交表单
- 检查工作流是否正常运行

## 📝 部署后检查清单

- [ ] 应用可以正常访问
- [ ] API 端点正常工作
- [ ] 前端资源加载正常
- [ ] SSL 证书有效
- [ ] 错误日志正常
- [ ] 性能监控设置
- [ ] 备份策略配置

## 🆘 常见问题

### 前端显示空白页

**解决方案**：
1. 检查 `frontend/dist/` 是否存在
2. 检查浏览器控制台错误
3. 确认 API 基础 URL 配置正确

### API 调用失败

**解决方案**：
1. 检查 CORS 配置
2. 检查环境变量
3. 查看服务器日志

### 静态资源 404

**解决方案**：
1. 重新运行 `./build.sh`
2. 检查 `frontend/dist/assets/` 目录
3. 检查 Nginx 配置

## 📚 更多信息

详细部署说明请查看 `DEPLOYMENT.md`。
