# 🚀 快速开始指南

## Docker 部署（推荐）

### 前置条件
```bash
# 检查 Docker 是否安装
docker --version
docker-compose --version
```

### 一键启动
```bash
# 方式1：使用脚本（推荐新手）
./docker-start.sh

# 方式2：直接使用 docker-compose
docker-compose up -d

# 方式3：使用 Makefile
make up
```

### 访问系统
打开浏览器访问：**http://localhost**

---

## 常用命令速查

| 操作 | Docker Compose 命令 | Makefile 命令 |
|-----|-------------------|--------------|
| 🚀 启动服务 | `docker-compose up -d` | `make up` |
| 🛑 停止服务 | `docker-compose down` | `make down` |
| 🔄 重启服务 | `docker-compose restart` | `make restart` |
| 📋 查看日志 | `docker-compose logs -f` | `make logs` |
| 📊 查看状态 | `docker-compose ps` | `make ps` |
| 🔨 重新构建 | `docker-compose up -d --build` | `make rebuild` |
| 🧹 清理所有 | `docker-compose down --rmi all` | `make clean-all` |
| 🐚 进入后端 | `docker-compose exec backend bash` | `make shell-backend` |
| ❤️ 健康检查 | - | `make health` |

---

## 故障排查速查

### 问题1: 端口被占用
```bash
# 查找占用端口的进程
lsof -i :80        # 前端端口
lsof -i :5000      # 后端端口

# 修改端口（编辑 docker-compose.yml）
services:
  frontend:
    ports:
      - "8080:80"  # 改用 8080
```

### 问题2: 容器启动失败
```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 查看容器状态
docker-compose ps

# 重新构建（不使用缓存）
docker-compose build --no-cache
docker-compose up -d
```

### 问题3: 无法访问服务
```bash
# 检查容器是否运行
docker-compose ps

# 检查网络
docker network ls
docker network inspect stock-backtest-network

# 测试后端连接
curl http://localhost:5000/health

# 进入容器检查
docker-compose exec backend bash
docker-compose exec frontend sh
```

### 问题4: 回测功能报错
```bash
# 查看后端实时日志
docker-compose logs -f backend

# 进入后端容器测试
docker-compose exec backend python
>>> import akshare as ak
>>> ak.stock_info_a_code_name()
```

---

## 开发调试

### 查看实时日志
```bash
# 所有服务
docker-compose logs -f

# 仅后端
docker-compose logs -f backend

# 仅前端
docker-compose logs -f frontend

# 最近100行
docker-compose logs --tail=100
```

### 进入容器调试
```bash
# 后端容器
docker-compose exec backend bash
python  # 进入 Python 交互式环境

# 前端容器
docker-compose exec frontend sh
cat /etc/nginx/conf.d/default.conf  # 查看 nginx 配置
```

### 资源监控
```bash
# 查看资源使用
docker stats stock-backtest-backend stock-backtest-frontend

# 或使用 Makefile
make stats
```

---

## 生产环境配置

### 1. 修改环境变量
编辑 `docker-compose.yml`:
```yaml
services:
  backend:
    environment:
      - FLASK_ENV=production
      - DEFAULT_INITIAL_CAPITAL=100000
      - DEFAULT_COMMISSION_RATE=0.0003
```

### 2. 资源限制
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### 3. 日志配置
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 更多信息

- 📖 完整部署文档: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- 📝 项目主文档: [README.md](./README.md)
- 🛠️ Makefile 帮助: `make help`

---

## 一分钟快速测试

```bash
# 1. 启动服务
docker-compose up -d

# 2. 等待服务就绪（约30秒）
sleep 30

# 3. 测试后端健康
curl http://localhost:5000/health

# 4. 在浏览器中打开
open http://localhost  # macOS
# 或直接访问 http://localhost

# 5. 停止服务
docker-compose down
```

---

**祝您使用愉快！** 如有问题请查看 [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) 获取详细帮助。
