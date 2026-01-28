# 📤 GitHub 推送指南

## 当前状态

- ✅ Git 仓库已初始化
- ✅ 代码已提交（4 个提交，147 个文件）
- ✅ 远程仓库已配置: `https://github.com/MikeFan1433/ai-job-hunting-assistant`
- ⏳ 需要认证才能推送

## 🔐 认证方式

GitHub 推送需要认证，有两种方式：

### 方式 1: 使用 SSH（推荐）

如果你已经配置了 SSH key：

```bash
cd "AI Job Hunting Assistant"

# 使用 SSH URL
git remote set-url origin git@github.com:MikeFan1433/ai-job-hunting-assistant.git

# 推送
git push -u origin main
```

### 方式 2: 使用 Personal Access Token

1. **创建 Personal Access Token**:
   - 访问: https://github.com/settings/tokens
   - 点击 "Generate new token" → "Generate new token (classic)"
   - 设置权限: 至少勾选 `repo` 权限
   - 生成并复制 token

2. **使用 token 推送**:
```bash
cd "AI Job Hunting Assistant"

# 使用 HTTPS URL（带 token）
git remote set-url origin https://YOUR_TOKEN@github.com/MikeFan1433/ai-job-hunting-assistant.git

# 或使用 GitHub CLI
gh auth login
git push -u origin main
```

### 方式 3: 使用 GitHub CLI（最简单）

```bash
# 安装 GitHub CLI（如果还没有）
brew install gh

# 登录
gh auth login

# 推送
cd "AI Job Hunting Assistant"
git push -u origin main
```

## 📋 推送前检查清单

### 1. 确保 GitHub 仓库已创建

访问 https://github.com/new 创建仓库：
- **Repository name**: `ai-job-hunting-assistant`
- **Visibility**: **Public** (必须)
- **不要**初始化 README

### 2. 配置认证

选择上述三种方式之一配置认证。

### 3. 推送代码

```bash
cd "AI Job Hunting Assistant"
git push -u origin main
```

## 🚀 快速推送脚本

我已经创建了 `setup_github_repo.sh` 脚本，你可以运行：

```bash
./setup_github_repo.sh ai-job-hunting-assistant
```

## ⚠️ 常见问题

### 问题 1: "could not read Username"

**解决方案**: 需要配置认证（SSH 或 Personal Access Token）

### 问题 2: "repository not found"

**解决方案**: 
1. 确保在 GitHub 上已创建仓库
2. 确保仓库名称正确
3. 确保有推送权限

### 问题 3: "Permission denied"

**解决方案**: 
1. 检查 SSH key 是否正确配置
2. 检查 Personal Access Token 是否有 `repo` 权限
3. 确保仓库是公开的或你有访问权限

## 📝 推送后的下一步

推送成功后：

1. **验证代码已上传**:
   - 访问: https://github.com/MikeFan1433/ai-job-hunting-assistant
   - 确认所有文件都在

2. **执行部署**:
```bash
python3 deploy_to_ai_builders.py
```

提供信息：
- GitHub URL: `https://github.com/MikeFan1433/ai-job-hunting-assistant`
- Service Name: (例如: `ai-job-assistant`)
- Branch: `main`

---

**需要我帮你配置认证或执行推送吗？** 🚀
