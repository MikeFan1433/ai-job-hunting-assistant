# 🚀 AI Builders 部署指南

根据 [AI Builders 部署文档](https://space.ai-builders.com/deployments) 的要求，本指南将帮助你完成部署。

## 📋 部署前检查清单

### ✅ 已完成

1. **Dockerfile** ✅
   - 已创建并配置正确
   - 使用 shell form (`sh -c`) 支持 PORT 环境变量
   - 暴露端口 8000
   - 构建前端并服务静态文件

2. **前端构建** ✅
   - 前端已构建 (`frontend/dist/`)
   - 静态文件由后端 FastAPI 服务

3. **单进程/单端口** ✅
   - FastAPI 服务所有内容（API + 静态文件）
   - 无额外进程

4. **.gitignore** ✅
   - 已排除敏感文件（.env, node_modules 等）

## 🔑 部署所需信息

根据部署指南，我需要以下**三个关键信息**：

### 1. GitHub Repository URL
- **必须是公开的仓库**（私有仓库暂不支持）
- 格式：`https://github.com/username/repo-name`
- 例如：`https://github.com/yourusername/ai-job-hunting-assistant`

### 2. Service Name
- 部署服务的唯一名称
- **将成为你的子域名**：`https://{service-name}.ai-builders.space`
- 只能包含小写字母、数字和连字符
- 例如：`ai-job-assistant` 或 `job-hunting-assistant`

### 3. Git Branch
- 要部署的 Git 分支名称
- 通常是 `main`、`master` 或 `develop`
- **必须指定**，不能为空

## 📝 我可以帮你完成的工作

### ✅ 已完成

1. ✅ **修复 Dockerfile**
   - 使用 shell form (`sh -c`) 支持 PORT 环境变量
   - 格式：`CMD sh -c "gunicorn ... --bind 0.0.0.0:${PORT:-8000} ..."`
   - 健康检查也使用 PORT 环境变量

2. ✅ **验证部署准备**
   - 创建了 `deploy_check.py` 检查脚本
   - 所有检查已通过

3. ✅ **配置静态文件服务**
   - 后端已配置服务前端静态文件
   - 单进程架构符合要求

### 🔄 待完成（需要你的信息）

1. **初始化 Git 仓库**（如果还没有）
   - 创建 GitHub 仓库
   - 提交并推送代码

2. **执行部署**
   - 调用部署 API (`POST /v1/deployments`)
   - 监控部署状态

## 🚀 部署流程

### 步骤 1: 准备 GitHub 仓库

如果你还没有 GitHub 仓库：

```bash
# 初始化 Git 仓库
git init
git add .
git commit -m "Initial commit: AI Job Hunting Assistant"

# 在 GitHub 上创建新仓库（公开的）
# 然后添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

**重要**：
- 仓库必须是**公开的**
- 确保 `.env` 文件在 `.gitignore` 中（已配置）
- 不要提交敏感信息

### 步骤 2: 提供部署信息

请提供以下信息：

1. **GitHub Repository URL**: `https://github.com/...`
2. **Service Name**: `your-service-name`
3. **Git Branch**: `main` (或 `master`)

### 步骤 3: 执行部署

一旦你提供了上述信息，我将：

1. 验证仓库状态（确保代码已推送）
2. 调用部署 API
3. 监控部署进度
4. 提供部署后的访问链接

## 📊 部署 API 调用示例

部署 API 请求格式：

```json
{
  "repo_url": "https://github.com/username/repo-name",
  "service_name": "your-service-name",
  "branch": "main",
  "env_vars": {
    // 可选：额外的环境变量
    // AI_BUILDER_TOKEN 会自动注入，无需手动添加
  }
}
```

## ⚠️ 重要注意事项

1. **PORT 环境变量**
   - Koyeb 会在运行时设置 `PORT` 环境变量
   - Dockerfile 已配置使用 `${PORT:-8000}`
   - 应用代码无需修改（gunicorn 会自动使用）

2. **AI_BUILDER_TOKEN**
   - 部署时自动注入，无需手动配置
   - 你的应用可以通过 `os.getenv("AI_BUILDER_TOKEN")` 读取

3. **资源限制**
   - 256 MB RAM 限制
   - 已优化 Dockerfile（减少 workers 数量）

4. **部署时间**
   - 通常需要 5-10 分钟
   - 可以通过 Deployment Portal 或 API 查看状态

## 🎯 下一步

**请提供以下信息，我将帮你完成部署：**

1. GitHub Repository URL（公开仓库）
2. Service Name（将成为子域名）
3. Git Branch（例如：main）

或者，如果你还没有 GitHub 仓库，我可以先帮你：
- 初始化 Git 仓库
- 准备提交和推送
- 然后进行部署

---

**准备好了吗？请告诉我你的 GitHub 仓库信息，或者让我先帮你设置 Git 仓库！** 🚀
