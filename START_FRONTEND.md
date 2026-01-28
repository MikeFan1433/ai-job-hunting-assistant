# 如何启动前端应用

## 前置要求

1. **安装 Node.js**
   - 访问 https://nodejs.org/ 下载并安装 Node.js 18 或更高版本
   - 验证安装：`node --version` 和 `npm --version`

2. **确保后端 API 正在运行**
   - 后端应该运行在 `http://localhost:8000`
   - 如果使用不同的端口，需要修改 `frontend/src/services/api.ts` 中的 `API_BASE_URL`

## 启动步骤

### 1. 进入前端目录

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant/frontend"
```

### 2. 安装依赖

```bash
npm install
```

如果遇到网络问题，可以使用国内镜像：

```bash
npm install --registry=https://registry.npmmirror.com
```

### 3. 启动开发服务器

```bash
npm run dev
```

前端应用将在 `http://localhost:3000` 启动。

### 4. 在浏览器中打开

访问 `http://localhost:3000` 即可使用应用。

## 启动后端 API

在另一个终端窗口中：

```bash
cd "/Users/mikefan/Desktop/AI Architect - Superlinear/AI Job Hunting Assistant"
python3 -m uvicorn workflow_api:app --reload --port 8000
```

## 常见问题

### 问题 1: `npm: command not found`

**解决方案**: 需要安装 Node.js。访问 https://nodejs.org/ 下载安装。

### 问题 2: 端口 3000 已被占用

**解决方案**: 
- 修改 `frontend/vite.config.ts` 中的 `server.port`
- 或者关闭占用端口 3000 的其他应用

### 问题 3: 无法连接到后端 API

**解决方案**:
1. 确保后端正在运行：`curl http://localhost:8000/api/v1/health`
2. 检查 `frontend/src/services/api.ts` 中的 `API_BASE_URL`
3. 检查后端的 CORS 设置

### 问题 4: 依赖安装失败

**解决方案**:
```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

## 生产环境构建

如果需要构建生产版本：

```bash
npm run build
```

构建产物将在 `frontend/dist` 目录中。

## 开发提示

- 前端代码修改后会自动热重载
- 查看浏览器控制台了解错误信息
- 使用 React DevTools 调试组件状态
