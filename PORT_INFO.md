# 🔌 端口管理中枢

> 本文档统一管理所有项目的端口配置，避免端口冲突。

## 📋 所有项目端口使用概览

| 项目 | 端口范围 | 状态 |
|------|---------|------|
| **web3-demo** | 3000 | ✅ 运行中 |
| **my-first-dapp** | 3001 | ✅ 已配置 |
| **stock_pal** | 4000-4001, 4080, 5432 | ✅ 已配置 |
| **pigeon_web** | 2776, 5000-5002, 5173, 5175, 5433-5434, 6380-6381, 8081, 8380-8381, 8386, 8388, 8390-8391, 8396, 8398 | ✅ 已占用 |

---

## 1️⃣ Web3-Demo 项目

### 使用端口

- **Vite 开发服务器**: `3000` ✅ 无冲突

### 配置信息

- 配置位置: `vite.config.js:8`
- 访问地址: http://localhost:3000
- 项目路径: `/Users/yukun-admin/projects/web3/web3-demo`

---

## 2️⃣ My-First-DApp 项目

### 使用端口

**Docker 环境:**
- Nginx 静态服务器: `3001` ✅ 无冲突

### 配置信息

- 配置位置: `docker-compose.yml`
- 访问地址: http://localhost:3001
- 项目路径: `/Users/yukun-admin/projects/web3/my-first-dapp`
- 说明: 第一个 Web3 应用，连接 MetaMask 钱包

### 启动方式

```bash
cd /Users/yukun-admin/projects/web3/my-first-dapp
docker-compose up -d
```

---

## 3️⃣ Stock_Pal 项目

### 使用端口

**开发环境:**
- 前端 Vite: `4000` ✅ 无冲突
- 后端 Flask: `4001` ✅ 无冲突

**Docker 环境:**
- Frontend: `4080` ✅ 无冲突
- Backend: `4001` ✅ 无冲突
- PostgreSQL: `5432` ✅ 无冲突（PostgreSQL 标准端口）

### 配置信息

- 项目路径: `/Users/yukun-admin/projects/stock_pal`
- 前端访问: http://localhost:4000 (开发) / http://localhost:4080 (Docker)
- 后端 API: http://localhost:4001
- PostgreSQL: localhost:5432
  - 数据库名: `stockpal`
  - 用户名: `stockpal`
  - 密码: `stockpal_dev_2024` (仅用于开发环境)
- 详细文档: `/Users/yukun-admin/projects/stock_pal/PORT_INFO.md`

### 访问 PostgreSQL

```bash
# 方式1: 从 Docker 容器访问
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal

# 方式2: 从宿主机访问（需要安装 psql 客户端）
psql -h localhost -p 5432 -U stockpal -d stockpal

# 方式3: 进入容器后访问
docker exec -it stock-backtest-postgres bash
psql -U stockpal -d stockpal
```

---

## 4️⃣ Pigeon_Web 项目

本项目经过完整的端口冲突检查，确保与 pigeon_web 项目的所有环境（本地开发、E2E 测试、Integration 测试）都没有端口冲突。

### pigeon_web 项目使用的所有端口

#### 1. 本地开发环境

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端 Vite | 5173 | 开发服务器 |
| Flask 后端 | 5000 | API 服务 |
| Redis | 6380 | 缓存服务 |
| PostgreSQL | 5433 | 数据库 |
| Zookeeper | 8381 | 分布式协调 |
| HTTP Gateway | 8081 | 消息网关 |

#### 2. E2E 测试环境（Docker 容器）

位置: `/Users/yukun-admin/projects/pigeon/pigeon_web/tests/e2e/docker`

| 服务 | 宿主机端口 | 容器端口 | 用途 |
|------|-----------|---------|------|
| PostgreSQL | 5433 | 5432 | 测试数据库 |
| Redis | 6380 | 6379 | 缓存服务 |
| Zookeeper Client | 8381 | 2181 | ZK 客户端端口 |
| Zookeeper Follower | 8386 | 2888 | ZK Follower |
| Zookeeper Election | 8388 | 3888 | ZK 选举 |
| Zookeeper Admin | 8380 | 8080 | ZK 管理端口 |
| Gateway SMPP | 2776 | 2775 | SMPP 网关 |
| Gateway HTTP | 8081 | 8080 | HTTP 网关 |
| Backend API | 5001 | 5000 | Flask 后端 |
| Frontend | 5175 | 80 | Nginx 前端 |

#### 3. Integration 测试环境（Docker 容器）

位置: `/Users/yukun-admin/projects/pigeon/pigeon_web/tests/integration/docker`

| 服务 | 宿主机端口 | 容器端口 | 用途 |
|------|-----------|---------|------|
| PostgreSQL | 5434 | 5432 | 测试数据库 |
| Redis | 6381 | 6379 | 缓存服务 |
| Zookeeper Client | 8391 | 2181 | ZK 客户端端口 |
| Zookeeper Follower | 8396 | 2888 | ZK Follower |
| Zookeeper Election | 8398 | 3888 | ZK 选举 |
| Zookeeper Admin | 8390 | 8080 | ZK 管理端口 |
| Backend API | 5002 | 5000 | Flask 后端 |

### 所有被占用的端口汇总

```
2776, 5000, 5001, 5002, 5173, 5175, 5433, 5434,
6380, 6381, 8081, 8380, 8381, 8386, 8388, 8390,
8391, 8396, 8398
```

### 配置信息

- 项目路径: `/Users/yukun-admin/projects/pigeon/pigeon_web`
- 前端访问: http://localhost:5173 (开发)
- 后端 API: http://localhost:5000

---

## 📊 端口占用总览表

| 端口 | 项目 | 用途 | 环境 |
|------|------|------|------|
| 3000 | web3-demo | Vite 开发服务器 | 开发 |
| 3001 | my-first-dapp | Nginx 静态服务器 | Docker |
| 4000 | stock_pal | 前端开发服务器 | 开发 |
| 4001 | stock_pal | 后端 API | 开发/Docker |
| 4080 | stock_pal | 前端 Nginx | Docker |
| 5432 | stock_pal | PostgreSQL | Docker |
| 2776 | pigeon_web | SMPP Gateway | E2E Docker |
| 5000 | pigeon_web | Flask 后端 | 本地开发 |
| 5001 | pigeon_web | Flask 后端 | E2E Docker |
| 5002 | pigeon_web | Flask 后端 | Integration Docker |
| 5173 | pigeon_web | Vite 前端 | 本地开发 |
| 5175 | pigeon_web | Nginx 前端 | E2E Docker |
| 5433 | pigeon_web | PostgreSQL | 本地开发/E2E |
| 5434 | pigeon_web | PostgreSQL | Integration |
| 6380 | pigeon_web | Redis | 本地开发/E2E |
| 6381 | pigeon_web | Redis | Integration |
| 8081 | pigeon_web | HTTP Gateway | 本地开发/E2E |
| 8380 | pigeon_web | Zookeeper Admin | E2E |
| 8381 | pigeon_web | Zookeeper Client | 本地开发/E2E |
| 8386 | pigeon_web | Zookeeper Follower | E2E |
| 8388 | pigeon_web | Zookeeper Election | E2E |
| 8390 | pigeon_web | Zookeeper Admin | Integration |
| 8391 | pigeon_web | Zookeeper Client | Integration |
| 8396 | pigeon_web | Zookeeper Follower | Integration |
| 8398 | pigeon_web | Zookeeper Election | Integration |

---

## 🎯 端口分配策略

### 已分配端口范围

- **3000-3999**: Web3 相关项目
  - 3000: web3-demo
  - 3001: my-first-dapp

- **4000-4999**: 股票/金融相关项目
  - 4000-4001: stock_pal 开发环境
  - 4080: stock_pal Docker 环境

- **5000-5999**: Pigeon 项目主服务
  - 5000-5002: 后端 Flask API
  - 5173, 5175: 前端服务
  - 5433-5434: PostgreSQL

- **6000-6999**: 缓存服务
  - 6380-6381: Redis

- **8000-8999**: 中间件和网关
  - 8081: HTTP Gateway
  - 8380-8398: Zookeeper 集群

### 推荐端口分配

如需添加新项目，建议按以下规则分配端口：

1. **Web 前端**: 3000-4999 范围
2. **API 后端**: 5000-5999 范围
3. **数据库**: 5400-5499, 3306, 5432 等
4. **缓存**: 6379-6399 范围
5. **消息队列**: 5672, 15672 等
6. **中间件**: 8000-8999 范围

---

## 🔧 端口检查和管理

### 检查端口占用

```bash
# macOS/Linux - 检查特定端口
lsof -i :3000

# 检查多个端口
lsof -i :3000 -i :4000 -i :5000

# 查看端口占用的详细信息
netstat -an | grep LISTEN | grep -E ":(3000|4000|5000)"
```

### 释放端口

```bash
# 找到占用端口的进程
lsof -ti :3000

# 杀死进程
kill -9 $(lsof -ti :3000)
```

### 批量检查项目端口

```bash
# 检查 web3-demo 端口
lsof -i :3000

# 检查 my-first-dapp 端口
lsof -i :3001

# 检查 stock_pal 端口
lsof -i :4000 -i :4001 -i :4080

# 检查 pigeon_web 端口
lsof -i :5000 -i :5173 -i :5433 -i :6380 -i :8381
```

---

## 📝 修改端口指南

### Web3-Demo

编辑 `vite.config.js`:
```javascript
server: {
  port: 3000,  // 修改这里
  host: '0.0.0.0',
}
```

### Stock_Pal

详见: `/Users/yukun-admin/projects/stock_pal/PORT_INFO.md`

### Pigeon_Web

根据需要修改对应环境的配置文件。

---

## ⚠️ 注意事项

1. **修改端口前**: 确保新端口未被占用
2. **修改端口后**:
   - 重启开发服务器或重新构建 Docker 容器
   - 更新相关文档中的端口引用
   - 通知团队成员
3. **避免使用**: 系统保留端口（0-1023）和常见服务端口
4. **端口冲突**: 如遇冲突，优先修改新项目的端口

---

## 📚 相关文档

- Web3-Demo: `/Users/yukun-admin/projects/web3/web3-demo/`
- Stock_Pal: `/Users/yukun-admin/projects/stock_pal/PORT_INFO.md`
- Pigeon_Web: `/Users/yukun-admin/projects/pigeon/pigeon_web/`

---

**最后更新**: 2025-11-16
**管理员**: 端口管理中枢
