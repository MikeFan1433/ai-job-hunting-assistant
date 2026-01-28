# AI Job Hunting Assistant

一个智能求职助手应用，提供简历优化、JD分析和面试准备功能。

## 🚀 功能特性

- **简历优化**: AI 驱动的简历优化建议
- **JD 分析**: 深度分析职位描述，生成匹配度报告
- **项目包装**: 智能项目经验优化
- **面试准备**: 个性化面试问题准备

## 📋 技术栈

### 后端
- Python 3.8+
- FastAPI
- Uvicorn / Gunicorn
- OpenAI API

### 前端
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Zustand (状态管理)

## 🛠️ 安装和运行

### 前置要求

- Python 3.8+
- Node.js 18+
- npm 或 yarn

### 快速开始

1. **克隆仓库**
```bash
git clone <repository-url>
cd "AI Job Hunting Assistant"
```

2. **安装后端依赖**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **安装前端依赖**
```bash
cd frontend
npm install
cd ..
```

4. **配置环境变量**

创建 `.env` 文件：
```bash
STUDENT_PORTAL_BASE_URL=https://space.ai-builders.com/backend
STUDENT_PORTAL_API_KEY=your-api-key-here
```

5. **启动后端**
```bash
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000
```

6. **启动前端（开发模式）**
```bash
cd frontend
npm run dev
```

访问 http://localhost:3000

## 🏗️ 生产环境构建

### 构建前端

```bash
./build.sh
```

### 启动生产服务器

```bash
./deploy.sh
```

访问 http://localhost:8000

## 🌐 部署

### 部署到 ai-builders.space

详细部署指南请参考：
- `DEPLOY_TO_AI_BUILDERS.md` - 完整部署指南
- `QUICK_DEPLOY.md` - 快速部署步骤

### 使用 Docker

```bash
docker build -t ai-job-assistant .
docker-compose up -d
```

## 📚 文档

- `DEPLOYMENT.md` - 完整部署指南
- `DEPLOY_TO_AI_BUILDERS.md` - ai-builders.space 部署指南
- `QUICK_DEPLOY.md` - 快速部署指南
- `HOW_TO_START.md` - 启动指南

## 🧪 测试

```bash
# 测试配置
python3 test_deployment.py

# 测试 API
python3 test_api.py
```

## 📝 API 文档

启动后端后，访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/v1/health

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- 在线演示: https://your-app.ai-builders.space
- API 文档: http://localhost:8000/docs
