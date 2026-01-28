# 🚀 快速分享指南

## 三步分享你的应用

### 1️⃣ 启动后端（终端 1）

```bash
./start_backend.sh
```

或者：

```bash
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000
```

### 2️⃣ 启动前端（终端 2）

```bash
cd frontend
npm run dev
```

启动后会显示：
```
➜  Local:   http://localhost:3000/
➜  Network: http://192.168.x.x:3000/
```

### 3️⃣ 获取分享链接

运行：

```bash
./get_share_url.sh
```

会显示类似：
```
📱 分享链接: http://192.168.1.183:3000
```

把这个链接分享给朋友即可！

## ✅ 使用条件

- ✅ 朋友和你在**同一个 WiFi 网络**下
- ✅ 后端和前端都在运行
- ✅ 防火墙允许端口 3000 和 8000

## 🔍 检查清单

如果朋友无法访问：

1. **检查后端是否运行**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **检查 IP 地址**
   ```bash
   ./get_share_url.sh
   ```

3. **检查防火墙**
   - macOS: 系统偏好设置 > 安全性与隐私 > 防火墙
   - 确保允许端口 3000 和 8000

4. **确保同一网络**
   - 朋友必须连接同一个 WiFi
   - 不能使用手机热点（除非朋友也连你的热点）

## 📱 手机访问

如果你想在手机上测试：

1. 确保手机和电脑在同一 WiFi
2. 在手机浏览器输入：`http://你的IP:3000`
3. 例如：`http://192.168.1.183:3000`

## 🌐 跨网络分享（高级）

如果朋友不在同一网络，可以使用内网穿透：

### 使用 ngrok

```bash
# 安装 ngrok
brew install ngrok  # macOS
# 或访问 https://ngrok.com/download

# 启动应用后，创建隧道
ngrok http 3000
```

会得到一个公网 URL，例如：`https://abc123.ngrok.io`

**注意：** 需要同时为后端创建隧道，并修改前端 API 配置。

## 💡 提示

- 你的 IP 地址可能会变化（DHCP）
- 每次分享前可以运行 `./get_share_url.sh` 获取最新链接
- 如果 IP 变化，需要重新分享新链接
