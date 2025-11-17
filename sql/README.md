# SQL 数据库管理

Stock Pal 系统的数据库结构定义与管理脚本。

---

## 📁 目录结构

```
sql/
├── modules/                    # 数据库模块（按功能分离）
│   ├── 01_stock_data_cache.sql      # 股票数据缓存
│   ├── 02_backtest_results.sql      # 回测结果存储
│   ├── 03_user_management.sql       # 用户管理（预留）
│   ├── 04_watchlist.sql             # 观察列表与提醒（预留）
│   └── README.md                    # 模块使用说明
└── init_db.sh                  # 自动化初始化脚本
```

---

## 🚀 快速开始

### 方式1: 使用自动化脚本（推荐）

```bash
# 在 Docker 容器中初始化数据库
docker exec -it stock-backtest-backend /bin/bash
cd /app
./sql/init_db.sh

# 或从宿主机执行
docker exec -it stock-backtest-backend bash -c "cd /app && ./sql/init_db.sh"
```

### 方式2: 手动执行模块SQL

```bash
# 进入 PostgreSQL 容器
docker exec -it stock-backtest-postgres bash

# 逐个模块执行
psql -U stockpal -d stockpal -f /path/to/01_stock_data_cache.sql
psql -U stockpal -d stockpal -f /path/to/02_backtest_results.sql
# ... 依次执行其他模块
```

### 方式3: 通过代码自动创建（当前使用）

```python
# Python代码会自动初始化数据库
from app.services.cache_service import CacheService
cache = CacheService()  # 自动创建 stock_data 和 data_sync_log 表
```

---

## 📊 数据库模块

### ✅ 已实现模块

#### 1. 股票数据缓存 (`01_stock_data_cache.sql`)
- **表**: `stock_data`, `data_sync_log`
- **功能**: 缓存AkShare获取的股票历史行情数据
- **代码**: `backend/app/services/cache_service.py`
- **状态**: ✅ 生产使用中

**主要表结构**:
```sql
-- 股票历史数据
stock_data (symbol, date, open, high, low, close, volume, ...)

-- 数据同步日志
data_sync_log (symbol, first_date, last_date, record_count)
```

### 🔶 设计中模块

#### 2. 回测结果存储 (`02_backtest_results.sql`)
- **表**: `backtest_runs`, `backtest_trades`, `backtest_equity_curve`
- **功能**: 存储回测配置、交易记录、权益曲线
- **设计**: 见 `doc/design/backtest_engine_upgrade_design.md`
- **状态**: 🔶 设计完成，待实现

**主要表结构**:
```sql
-- 回测运行记录
backtest_runs (id, strategy_id, symbol, metrics, config, ...)

-- 交易明细
backtest_trades (backtest_id, symbol, side, price, quantity, ...)

-- 权益曲线
backtest_equity_curve (backtest_id, date, equity, capital, ...)
```

### 📋 预留模块

#### 3. 用户管理 (`03_user_management.sql`)
- **表**: `users`, `user_sessions`, `user_preferences`
- **功能**: 用户注册、登录、权限管理
- **状态**: 📋 多用户版本预留

#### 4. 观察列表与提醒 (`04_watchlist.sql`)
- **表**: `watchlists`, `watchlist_items`, `price_alerts`, `alert_logs`
- **功能**: 自选股管理、价格提醒、通知推送
- **状态**: 📋 PRD需求已定义，待实现

---

## 🗄️ 数据库信息

### 当前配置
- **类型**: PostgreSQL 15
- **容器**: stock-backtest-postgres
- **数据库名**: stockpal
- **用户**: stockpal
- **端口**: 5432
- **持久化**: Docker volume (postgres-data)
- **字符编码**: UTF-8
- **外键约束**: 已启用

### 性能优化
PostgreSQL 15 提供了现代化的查询优化器和高级特性：
```sql
-- 查看数据库配置
SHOW shared_buffers;
SHOW work_mem;
SHOW effective_cache_size;

-- 启用查询计划分析
EXPLAIN ANALYZE SELECT * FROM stock_data WHERE symbol='000001';

-- 查看表大小
SELECT pg_size_pretty(pg_total_relation_size('stock_data'));
```

---

## 🛠️ 维护命令

### 查看数据库信息

```bash
# 连接到 PostgreSQL
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal

# 查看所有表
\dt

# 查看表结构
\d stock_data

# 查看数据统计
SELECT COUNT(*) FROM stock_data;

# 查看表大小
SELECT pg_size_pretty(pg_total_relation_size('stock_data'));
```

### 备份与恢复

```bash
# 备份数据库
docker exec stock-backtest-postgres pg_dump -U stockpal stockpal > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i stock-backtest-postgres psql -U stockpal stockpal < backup.sql

# 备份到容器内（然后复制出来）
docker exec stock-backtest-postgres pg_dump -U stockpal -F c -f /tmp/backup.dump stockpal
docker cp stock-backtest-postgres:/tmp/backup.dump ./backup.dump
```

### 数据清理

```bash
# 清理1年前的数据
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "DELETE FROM stock_data WHERE date < CURRENT_DATE - INTERVAL '1 year';"

# 回收空间（VACUUM）
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c "VACUUM FULL stock_data;"

# 重建索引
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c "REINDEX TABLE stock_data;"

# 分析表（更新统计信息）
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c "ANALYZE stock_data;"
```

### 查询示例

```bash
# 查询缓存统计
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal <<EOF
SELECT
    COUNT(DISTINCT symbol) as stock_count,
    COUNT(*) as total_records,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
FROM stock_data;
EOF

# 查询某只股票
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "SELECT * FROM stock_data WHERE symbol='000001' LIMIT 10;"

# 查看同步日志
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "SELECT * FROM data_sync_log ORDER BY updated_at DESC;"
```

---

## 📈 数据库迁移

### 迁移历史

**2025-11-16: SQLite → PostgreSQL 迁移完成**

系统已从 SQLite 迁移到 PostgreSQL 15，获得以下优势：
- ✅ 真正的并发支持（多用户同时访问）
- ✅ JSONB 类型支持（高效存储和查询 JSON 数据）
- ✅ 高级索引类型（GIN, GIST, BRIN等）
- ✅ 触发器和存储过程（业务逻辑数据库端实现）
- ✅ 更好的性能和扩展性
- ✅ 完整的 ACID 事务支持
- ✅ 丰富的数据类型（UUID, INET, 数组等）

### 迁移步骤（如需要从旧版本迁移数据）

**从 SQLite 导入到 PostgreSQL**:
```bash
# 1. 导出 SQLite 数据
sqlite3 data/stock_cache.db .dump > sqlite_dump.sql

# 2. 使用 pgloader (推荐)
# 安装 pgloader: brew install pgloader (macOS)
pgloader data/stock_cache.db postgresql://stockpal:stockpal_dev_2024@localhost:5432/stockpal

# 3. 或手动转换并导入
# 注意：需要调整SQL语法差异
# - INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL
# - REAL → NUMERIC
# - TEXT → VARCHAR/TEXT
# - DATETIME → TIMESTAMP

# 4. 验证数据
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "SELECT COUNT(*) FROM stock_data;"
```

---

## 🔍 故障排查

### 问题1: "connection refused"
**原因**: PostgreSQL 容器未启动或端口未暴露
**解决**:
```bash
# 检查容器状态
docker ps | grep postgres

# 启动 PostgreSQL 容器
docker-compose up -d postgres

# 查看日志
docker logs stock-backtest-postgres
```

### 问题2: 数据库容量过大
**解决**:
```bash
# 1. 清理旧数据
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "DELETE FROM stock_data WHERE date < CURRENT_DATE - INTERVAL '2 years';"

# 2. 执行 VACUUM FULL
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "VACUUM FULL;"

# 3. 查看数据库大小
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "SELECT pg_size_pretty(pg_database_size('stockpal'));"
```

### 问题3: 查询性能慢
**解决**:
```bash
# 1. 分析查询计划
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "EXPLAIN ANALYZE SELECT * FROM stock_data WHERE symbol='000001';"

# 2. 更新表统计信息
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "ANALYZE stock_data;"

# 3. 检查是否缺少索引
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "SELECT * FROM pg_indexes WHERE tablename='stock_data';"
```

### 问题4: 外键约束错误
**解决**:
```bash
# 检查外键约束
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "SELECT conname, conrelid::regclass, confrelid::regclass
   FROM pg_constraint WHERE contype = 'f';"

# 查看违反约束的数据
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "SELECT * FROM backtest_trades WHERE backtest_id NOT IN (SELECT id FROM backtest_runs);"
```

---

## 📚 相关文档

- [数据库模块详细说明](./modules/README.md)
- [回测结果存储backlog](../doc/backlog/回测结果存储与历史查询.md)
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/15/)
- [PostgreSQL 性能调优](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [psql 命令参考](https://www.postgresql.org/docs/current/app-psql.html)

---

## 🔄 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2024-10-30 | 初始版本，SQLite 股票数据缓存模块 |
| v1.1 | 2025-11-12 | 添加回测结果存储模块设计 |
| v1.2 | 2025-11-12 | 规范化SQL模块结构，添加文档 |
| v2.0 | 2025-11-16 | **重大更新**：从 SQLite 迁移到 PostgreSQL 15 |

---

**维护人员**: 开发团队
**最后更新**: 2025-11-16
