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
# 初始化数据库（默认路径：data/stock_cache.db）
./sql/init_db.sh

# 或指定数据库路径
./sql/init_db.sh /custom/path/to/database.db
```

### 方式2: 手动执行模块SQL

```bash
# 逐个模块执行
sqlite3 data/stock_cache.db < sql/modules/01_stock_data_cache.sql
sqlite3 data/stock_cache.db < sql/modules/02_backtest_results.sql
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
- **类型**: SQLite 3
- **文件**: `data/stock_cache.db`
- **大小**: 动态增长（视缓存数据量）
- **WAL模式**: 已启用（提升并发性能）
- **外键约束**: 已启用

### 性能优化
```sql
PRAGMA journal_mode = WAL;       -- 写前日志，提升并发
PRAGMA synchronous = NORMAL;     -- 平衡性能与安全
PRAGMA cache_size = -2000;       -- 2MB缓存
PRAGMA busy_timeout = 5000;      -- 5秒锁等待
```

---

## 🛠️ 维护命令

### 查看数据库信息

```bash
# 查看所有表
sqlite3 data/stock_cache.db ".tables"

# 查看表结构
sqlite3 data/stock_cache.db ".schema stock_data"

# 查看数据统计
sqlite3 data/stock_cache.db "SELECT COUNT(*) FROM stock_data;"
```

### 备份与恢复

```bash
# 备份数据库
cp data/stock_cache.db data/stock_cache.db.backup_$(date +%Y%m%d)

# 导出为SQL
sqlite3 data/stock_cache.db .dump > backup.sql

# 从SQL恢复
sqlite3 data/stock_cache.db < backup.sql
```

### 数据清理

```bash
# 清理1年前的数据
sqlite3 data/stock_cache.db "DELETE FROM stock_data WHERE date < date('now', '-1 year');"

# 回收空间
sqlite3 data/stock_cache.db "VACUUM;"

# 重建索引
sqlite3 data/stock_cache.db "REINDEX;"
```

### 查询示例

```bash
# 查询缓存统计
sqlite3 data/stock_cache.db <<EOF
SELECT
    COUNT(DISTINCT symbol) as stock_count,
    COUNT(*) as total_records,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
FROM stock_data;
EOF

# 查询某只股票
sqlite3 data/stock_cache.db "SELECT * FROM stock_data WHERE symbol='000001' LIMIT 10;"

# 查看同步日志
sqlite3 data/stock_cache.db "SELECT * FROM data_sync_log ORDER BY updated_at DESC;"
```

---

## 📈 数据库迁移

### 未来迁移计划

当满足以下条件时，考虑迁移到 **PostgreSQL** 或 **MySQL**：
- [ ] 多用户并发访问（>10用户）
- [ ] 数据量 >10GB
- [ ] 需要分布式部署
- [ ] 需要复杂查询优化

### 迁移步骤

**SQLite → PostgreSQL**:
```bash
# 1. 使用 pgloader
pgloader data/stock_cache.db postgresql://user:pass@localhost/stock_pal

# 2. 或手动迁移
sqlite3 data/stock_cache.db .dump > dump.sql
# 调整SQL语法（AUTOINCREMENT → SERIAL等）
psql -U user -d stock_pal -f dump.sql
```

---

## 🔍 故障排查

### 问题1: "database is locked"
**原因**: 多个进程同时写入
**解决**:
```sql
-- 增加超时时间
PRAGMA busy_timeout = 10000;

-- 或启用WAL模式
PRAGMA journal_mode = WAL;
```

### 问题2: 数据库文件过大
**解决**:
```bash
# 1. 清理旧数据
sqlite3 data/stock_cache.db "DELETE FROM stock_data WHERE date < date('now', '-2 years');"

# 2. 回收空间
sqlite3 data/stock_cache.db "VACUUM;"

# 3. 查看文件大小
du -h data/stock_cache.db
```

### 问题3: 外键约束错误
**解决**:
```sql
-- 检查外键是否启用
PRAGMA foreign_keys;

-- 启用外键
PRAGMA foreign_keys = ON;
```

---

## 📚 相关文档

- [数据库模块详细说明](./modules/README.md)
- [回测引擎设计文档](../doc/design/backtest_engine_upgrade_design.md)
- [产品需求文档](../doc/requirements/product_requirements_stock_pal.md)
- [SQLite 官方文档](https://www.sqlite.org/docs.html)

---

## 🔄 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2024-10-30 | 初始版本，股票数据缓存模块 |
| v1.1 | 2025-11-12 | 添加回测结果存储模块设计 |
| v1.2 | 2025-11-12 | 规范化SQL模块结构，添加文档 |

---

**维护人员**: 开发团队
**最后更新**: 2025-11-12
