# 分享应用指南

## 🌐 如何让别人访问你的应用

### 方法 1: 局域网访问（最简单）

如果你的朋友和你在同一个局域网（WiFi）下，可以直接通过你的 IP 地址访问。

#### 步骤：

1. **获取你的 IP 地址**

   **macOS/Linux:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
   或者
   ```bash
   ipconfig getifaddr en0  # macOS
   ```

   **Windows:**
   ```cmd
   ipconfig
   ```
   找到 "IPv4 地址"，通常是 `192.168.x.x` 或 `10.x.x.x`

2. **启动后端（监听所有接口）**
   ```bash
   python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000
   ```
   或使用脚本：
   ```bash
   ./start_backend.sh
   ```

3. **启动前端**
   ```bash
   cd frontend
   npm run dev
   ```
   前端会显示：
   ```
   ➜  Local:   http://localhost:3000/
   ➜  Network: http://192.168.x.x:3000/
   ```

4. **分享链接**
   - 你的访问地址：`http://你的IP地址:3000`
   - 例如：`http://192.168.1.100:3000`
   - 把这个链接分享给局域网内的朋友

### 方法 2: 使用内网穿透（跨网络访问）

如果朋友不在同一个网络，可以使用内网穿透工具。

#### 使用 ngrok（推荐）

1. **安装 ngrok**
   ```bash
   # macOS
   brew install ngrok
   
   # 或访问 https://ngrok.com/download 下载
   ```

2. **启动你的应用**（后端和前端）

3. **创建隧道**
   ```bash
   # 为前端创建隧道
   ngrok http 3000
   
   # 会得到一个类似这样的 URL:
   # https://abc123.ngrok.io
   ```

4. **修改前端 API 配置**
   
   由于后端也在本地，需要为后端也创建隧道：
   ```bash
   # 终端 1: 前端隧道
   ngrok http 3000
   
   # 终端 2: 后端隧道
   ngrok http 8000
   ```

   然后修改 `frontend/src/services/api.ts`：
   ```typescript
   const API_BASE_URL = 'https://你的后端ngrok地址.ngrok.io';
   ```

5. **分享前端 ngrok URL**
   - 例如：`https://abc123.ngrok.io`
   - 把这个链接分享给任何人

#### 使用其他内网穿透工具

- **Cloudflare Tunnel** (免费)
- **localtunnel** (免费，npm 安装)
- **serveo** (免费，无需安装)

### 方法 3: 部署到云服务器（生产环境）

如果需要长期分享，建议部署到云服务器。

#### 快速部署选项：

1. **Vercel** (前端)
   ```bash
   cd frontend
   npm install -g vercel
   vercel
   ```

2. **Railway** (全栈)
   - 支持同时部署前端和后端
   - 自动配置域名

3. **Render** (全栈)
   - 免费 tier 可用
   - 自动 HTTPS

## 🔒 安全注意事项

1. **开发环境分享**
   - 当前配置允许所有来源访问（`allow_origins=["*"]`）
   - 仅用于开发和测试
   - 生产环境应该限制特定域名

2. **API 密钥保护**
   - 确保 `.env` 文件不被分享
   - 不要将 API 密钥提交到代码仓库

3. **防火墙设置**
   - 确保防火墙允许 3000 和 8000 端口
   - macOS: 系统偏好设置 > 安全性与隐私 > 防火墙

## 📱 移动设备访问

如果想让手机访问：

1. 确保手机和电脑在同一 WiFi
2. 使用电脑的 IP 地址访问
3. 例如：`http://192.168.1.100:3000`

## 🐛 常见问题

### 问题 1: 无法访问

**检查清单：**
- [ ] 后端是否在运行？
- [ ] 前端是否在运行？
- [ ] 防火墙是否允许端口 3000 和 8000？
- [ ] IP 地址是否正确？
- [ ] 是否在同一网络？

### 问题 2: CORS 错误

如果看到 CORS 错误，检查：
- 后端 `workflow_api.py` 中的 CORS 配置
- 确保 `allow_origins` 包含前端地址

### 问题 3: 连接被拒绝

**解决方案：**
1. 检查端口是否被占用
2. 确保使用 `0.0.0.0` 而不是 `localhost`
3. 检查防火墙设置

## 🚀 快速启动（分享模式）

```bash
# 终端 1: 启动后端
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000

# 终端 2: 启动前端
cd frontend
npm run dev

# 查看你的 IP 地址
ifconfig | grep "inet " | grep -v 127.0.0.1

# 分享链接: http://你的IP:3000
```

## 📝 示例

假设你的 IP 是 `192.168.1.100`：

1. 启动应用后
2. 分享链接：`http://192.168.1.100:3000`
3. 朋友在浏览器打开即可使用

**注意：** 确保朋友和你在同一个 WiFi 网络下！
