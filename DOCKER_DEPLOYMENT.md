# 🐳 Docker 部署文档

本文档介绍如何使用 Docker 和 Docker Compose 部署股票回测系统。

## 📋 前置要求

确保您的系统已安装以下软件：

- **Docker**: 20.10 或更高版本
- **Docker Compose**: 2.0 或更高版本

### 检查安装

```bash
docker --version
docker-compose --version
```

### 安装 Docker

- **macOS**: 下载并安装 [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Windows**: 下载并安装 [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- **Linux**: 参考 [Docker 官方文档](https://docs.docker.com/engine/install/)

---

## 🚀 快速启动

### 1. 克隆或进入项目目录

```bash
cd /Users/yukun-admin/projects/stock
```

### 2. 一键启动所有服务

```bash
docker-compose up -d
```

该命令会：
- 自动构建后端和前端镜像
- 启动所有容器
- 在后台运行服务

### 3. 查看服务状态

```bash
docker-compose ps
```

预期输出：
```
NAME                        IMAGE                      STATUS          PORTS
stock-backtest-backend      stock-backend              Up (healthy)    0.0.0.0:5000->5000/tcp
stock-backtest-frontend     stock-frontend             Up (healthy)    0.0.0.0:80->80/tcp
```

### 4. 访问系统

在浏览器中打开：**http://localhost**

---

## 📦 Docker 架构说明

### 服务组成

```
┌─────────────────────────────────────────────┐
│          浏览器访问 (localhost:80)           │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Frontend (Nginx)  │
         │  - React 应用      │
         │  - 静态文件服务    │
         │  - API 反向代理    │
         └─────────┬──────────┘
                   │ /api/* 请求
         ┌─────────▼──────────┐
         │  Backend (Flask)   │
         │  - RESTful API     │
         │  - 回测引擎        │
         │  - 数据获取        │
         └────────────────────┘
```

### 网络配置

- **stock-backtest-network**: 桥接网络，连接前后端服务
- **Frontend**: 监听宿主机 `80` 端口
- **Backend**: 内部暴露 `5000` 端口（通过 Nginx 代理访问）

### 容器说明

#### Backend 容器
- **基础镜像**: `python:3.11-slim`
- **工作目录**: `/app`
- **运行方式**: Gunicorn (4 workers, 120s timeout)
- **健康检查**: 每 30 秒检查 `/health` 端点

#### Frontend 容器
- **构建阶段**: `node:18-alpine` (编译 React 应用)
- **运行阶段**: `nginx:alpine` (提供静态文件服务)
- **Nginx 配置**:
  - 静态文件缓存 1 年
  - API 请求反向代理到 backend
  - SPA 路由支持
  - Gzip 压缩

---

## 🛠️ 常用命令

### 启动服务

```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 启动并查看实时日志
docker-compose up

# 仅启动特定服务
docker-compose up -d backend
docker-compose up -d frontend
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除所有数据（包括镜像）
docker-compose down --rmi all

# 停止并删除卷（如果有持久化数据）
docker-compose down -v
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart frontend
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 实时跟踪日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend

# 查看最近 100 行日志
docker-compose logs --tail=100
```

### 重新构建镜像

```bash
# 重新构建所有镜像
docker-compose build

# 重新构建特定服务
docker-compose build backend
docker-compose build frontend

# 不使用缓存重新构建
docker-compose build --no-cache

# 构建并启动
docker-compose up -d --build
```

### 进入容器

```bash
# 进入 backend 容器
docker-compose exec backend bash

# 进入 frontend 容器
docker-compose exec frontend sh

# 以 root 用户进入
docker-compose exec -u root backend bash
```

### 查看资源使用

```bash
# 查看容器资源使用情况
docker stats stock-backtest-backend stock-backtest-frontend

# 查看容器详细信息
docker inspect stock-backtest-backend
```

---

## 🔧 环境变量配置

### Backend 环境变量

在 `docker-compose.yml` 中的 `backend.environment` 部分配置：

```yaml
environment:
  - FLASK_ENV=production          # 运行环境
  - FLASK_DEBUG=False             # 调试模式
  - API_VERSION=v1                # API 版本
  - CORS_ORIGINS=http://localhost # 允许的跨域源
  - DATA_SOURCE=akshare           # 数据源
  - CACHE_EXPIRY=3600             # 缓存过期时间（秒）
  - DEFAULT_INITIAL_CAPITAL=100000    # 默认初始资金
  - DEFAULT_COMMISSION_RATE=0.0003    # 默认手续费率
```

### Frontend 环境变量

```yaml
environment:
  - API_BASE_URL=http://backend:5000  # 后端 API 地址
```

---

## 🐛 故障排查

### 1. 容器启动失败

**问题**: 容器启动后立即退出

**排查步骤**:
```bash
# 查看容器状态
docker-compose ps

# 查看容器日志
docker-compose logs backend
docker-compose logs frontend

# 查看容器退出原因
docker-compose logs --tail=50 backend
```

**常见原因**:
- 端口被占用（80 或 5000）
- 依赖安装失败
- 配置文件错误

### 2. 端口冲突

**问题**: `Bind for 0.0.0.0:80 failed: port is already allocated`

**解决方案**:

方法一：更改宿主机端口
```yaml
# 修改 docker-compose.yml
services:
  frontend:
    ports:
      - "8080:80"  # 使用 8080 端口
```

方法二：停止占用端口的服务
```bash
# macOS/Linux 查找占用端口的进程
sudo lsof -i :80
sudo kill -9 <PID>

# Windows
netstat -ano | findstr :80
taskkill /PID <PID> /F
```

### 3. 后端健康检查失败

**问题**: Backend 容器一直显示 `unhealthy`

**排查步骤**:
```bash
# 进入容器检查
docker-compose exec backend bash
curl http://localhost:5000/health

# 查看详细健康检查日志
docker inspect stock-backtest-backend | grep -A 10 Health
```

**常见原因**:
- Python 依赖安装不完整
- 网络连接问题
- 应用启动时间过长（调整 `start_period`）

### 4. 前端无法访问后端

**问题**: 前端页面加载，但回测功能报错

**排查步骤**:
```bash
# 检查网络连通性
docker-compose exec frontend ping backend

# 检查 Nginx 配置
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# 测试后端 API
curl http://localhost:5000/health
```

**解决方案**:
- 确保前后端在同一网络中
- 检查 Nginx 代理配置
- 查看浏览器开发者工具 Network 面板

### 5. 构建镜像速度慢

**问题**: `docker-compose build` 耗时很长

**解决方案**:

使用国内镜像源（修改 Dockerfile）:

**Backend Dockerfile**:
```dockerfile
# 添加 pip 国内镜像
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

**Frontend Dockerfile**:
```dockerfile
# 添加 npm 国内镜像
RUN npm config set registry https://registry.npmmirror.com && \
    npm ci --only=production
```

### 6. 数据获取失败

**问题**: 搜索股票或回测时报错 "Failed to fetch stock data"

**排查步骤**:
```bash
# 进入 backend 容器测试
docker-compose exec backend python
>>> import akshare as ak
>>> ak.stock_info_a_code_name()
```

**常见原因**:
- 网络连接问题（容器无法访问外网）
- AkShare 数据源暂时不可用
- 请求频率过高被限流

**解决方案**:
- 检查容器网络配置
- 等待一段时间后重试
- 添加请求缓存机制

---

## 📊 性能优化

### 1. 调整 Backend Workers

根据 CPU 核心数调整 Gunicorn workers:

```yaml
# docker-compose.yml
services:
  backend:
    command: gunicorn --bind 0.0.0.0:5000 --workers 8 --timeout 120 run:app
```

建议: `workers = (2 × CPU核心数) + 1`

### 2. 启用 Nginx 缓存

在 `frontend/nginx.conf` 中添加:

```nginx
# 添加缓存目录
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    # ... 其他配置
}
```

### 3. 资源限制

添加容器资源限制:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 🔄 生产环境部署建议

### 1. 使用环境变量文件

创建 `.env` 文件:

```bash
# .env
FLASK_ENV=production
BACKEND_PORT=5000
FRONTEND_PORT=80
INITIAL_CAPITAL=100000
COMMISSION_RATE=0.0003
```

更新 `docker-compose.yml`:

```yaml
services:
  backend:
    env_file:
      - .env
```

### 2. 启用 HTTPS

使用 Let's Encrypt + Nginx:

```yaml
services:
  nginx-proxy:
    image: jwilder/nginx-proxy
    ports:
      - "443:443"
    volumes:
      - /etc/nginx/certs
      - /etc/nginx/vhost.d
```

### 3. 添加监控

使用 Prometheus + Grafana:

```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 4. 日志管理

使用集中式日志系统（如 ELK Stack）:

```yaml
logging:
  driver: "fluentd"
  options:
    fluentd-address: "localhost:24224"
    tag: "stock-backtest"
```

### 5. 备份策略

如果添加数据持久化，定期备份:

```bash
# 备份卷数据
docker run --rm -v stock-backtest-data:/data -v $(pwd):/backup \
    alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz /data
```

---

## 📝 常见问答

### Q1: 如何更新代码？

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建并启动
docker-compose up -d --build

# 3. 查看更新后的日志
docker-compose logs -f
```

### Q2: 如何清理 Docker 资源？

```bash
# 停止并删除容器
docker-compose down

# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器、网络、卷
docker system prune -a --volumes

# 查看 Docker 占用空间
docker system df
```

### Q3: 如何在容器中执行 Python 命令？

```bash
# 进入容器
docker-compose exec backend bash

# 运行 Python
python

# 或直接执行命令
docker-compose exec backend python -c "import akshare as ak; print(ak.__version__)"
```

### Q4: 如何修改端口？

编辑 `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 改为 8080
```

然后重启:
```bash
docker-compose down
docker-compose up -d
```

### Q5: 如何查看容器内部文件？

```bash
# 复制文件到宿主机
docker cp stock-backtest-backend:/app/logs/app.log ./

# 或直接查看
docker-compose exec backend cat /app/logs/app.log
```

---

## 🎯 下一步

完成部署后，您可以：

1. ✅ 访问 http://localhost 开始使用系统
2. 📊 监控服务状态: `docker-compose ps`
3. 📝 查看日志: `docker-compose logs -f`
4. 🔧 根据需要调整配置和资源限制
5. 🚀 考虑生产环境的安全性和性能优化

---

## 📮 获取帮助

如遇到问题：

1. 查看本文档的故障排查部分
2. 检查容器日志: `docker-compose logs`
3. 提交 GitHub Issue 并附带日志信息
4. 参考 [Docker 官方文档](https://docs.docker.com/)

---

**祝您使用愉快！** 📈
