# 端口配置说明

## Stock_Pal 项目使用的端口

### 开发环境

- **前端 Vite 开发服务器**: `4000` ✅ 无冲突
  - 配置位置: `frontend/vite.config.ts:17`
  - 访问地址: http://localhost:4000

- **后端 Flask 开发服务器**: `4001` ✅ 无冲突
  - 配置位置: `backend/run.py:16`
  - API 地址: http://localhost:4001
  - 健康检查: http://localhost:4001/health

### Docker 生产环境

| 服务 | 宿主机端口 | 容器端口 | 用途 |
|------|-----------|---------|------|
| Frontend (Nginx) | 4080 | 80 | 前端服务 |
| Backend (Flask) | 4001 | 5000 | API 服务 |

配置位置: `docker-compose.yml`

## 端口冲突检查

本项目经过完整的端口冲突检查，确保与以下项目没有端口冲突：

### 与 pigeon_web 项目无冲突 ✅

**pigeon_web 占用端口汇总:**
```
本地开发: 5000, 5173, 5433, 6380, 8081, 8381
E2E 测试: 2776, 5001, 5175, 5433, 6380, 8081, 8380, 8381, 8386, 8388
Integration 测试: 5002, 5434, 6381, 8390, 8391, 8396, 8398
```

**stock_pal 使用端口:** 4000, 4001, 4080

### 与 web3-demo 项目无冲突 ✅

**web3-demo 占用端口:** 3000

**stock_pal 使用端口:** 4000, 4001, 4080

## 修改端口

如需修改端口，请同步修改以下文件：

### 1. 开发环境前端端口

编辑 `frontend/vite.config.ts`:
```typescript
server: {
  port: 4000,  // 修改这里
  host: '0.0.0.0',
  proxy: {
    '/api': {
      target: 'http://localhost:4001',  // 同步修改后端地址
      changeOrigin: true,
    },
  },
},
```

### 2. 开发环境后端端口

编辑 `backend/run.py`:
```python
port = int(os.environ.get('PORT', 4001))  # 修改这里或设置环境变量
```

或设置环境变量:
```bash
export PORT=4001
python backend/run.py
```

### 3. Docker 环境端口

编辑 `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "4001:5000"  # 修改宿主机端口（冒号前）

  frontend:
    ports:
      - "4080:80"    # 修改宿主机端口（冒号前）
```

同步更新 `.env.docker`:
```bash
BACKEND_PORT=4001
FRONTEND_PORT=4080
```

## 相关文档

修改端口后，需要同步更新以下文档中的端口引用：
- `README.md`
- `QUICK_START.md`
- `DOCKER_DEPLOYMENT.md`
- `/Users/yukun-admin/projects/web3/web3-demo/PORT_INFO.md` (端口管理中枢)

## 注意事项

1. 修改端口后需要重启开发服务器或重新构建 Docker 容器
2. 确保选择的端口未被系统其他服务占用
3. 端口范围建议在 1024-65535 之间
4. 避免使用已知的保留端口（如 3306 MySQL, 6379 Redis 等）
