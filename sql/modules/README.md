# SQL 模块说明

本目录包含 Stock Pal 系统的所有数据库模块定义。每个模块使用独立的 SQL 文件管理。

---

## 模块列表

| 文件 | 模块名称 | 状态 | 说明 |
|------|---------|------|------|
| `01_stock_data_cache.sql` | 股票数据缓存 | ✅ 已实现 | 缓存AkShare行情数据 |
| `02_backtest_results.sql` | 回测结果存储 | 🔶 设计中 | 存储回测运行记录 |
| `03_user_management.sql` | 用户管理 | 📋 预留 | 用户认证与授权（多用户版本） |
| `04_watchlist.sql` | 观察列表与提醒 | 📋 预留 | 自选股、价格提醒 |

**状态说明**：
- ✅ 已实现：代码已编写并在使用中
- 🔶 设计中：有详细设计文档，即将实现
- 📋 预留：需求已确定，未来版本实现

---

## 数据库类型

当前系统使用 **PostgreSQL 15**（Docker 容器：`stock-backtest-postgres`）

### PostgreSQL 特点
- ✅ 真正的并发支持（多用户同时访问）
- ✅ JSONB 类型（高效存储和查询 JSON 数据）
- ✅ 高级索引（GIN, GIST, BRIN 等）
- ✅ 触发器和存储过程
- ✅ 完整的 ACID 事务
- ✅ 丰富的数据类型（UUID, INET, 数组等）
- ✅ 出色的查询优化器
- ✅ 适合中大规模部署

### 迁移历史
- **2025-11-16**: 从 SQLite 迁移到 PostgreSQL 15
- 获得更好的并发性能、数据类型支持和扩展性

---

## 使用指南

### 1. 初始化数据库

**方式一：通过代码初始化（推荐）**
```python
# Python代码会自动创建表结构
from app.services.cache_service import CacheService
cache_service = CacheService()  # 自动调用 _init_database()
```

**方式二：手动执行SQL**
```bash
# 连接到 PostgreSQL 容器
docker exec -it stock-backtest-postgres bash

# 执行 SQL 文件
psql -U stockpal -d stockpal -f /path/to/01_stock_data_cache.sql

# 或从宿主机执行
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -f /sql/modules/01_stock_data_cache.sql
```

### 2. 查看表结构

```bash
# 连接到 PostgreSQL
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal

# 查看所有表
\dt

# 查看特定表结构
\d stock_data

# 查看表注释
\d+ stock_data

# 查看索引
\di

# 查看函数
\df
```

### 3. 查询示例

```sql
-- 进入 psql 后执行

-- 查询缓存统计
SELECT COUNT(DISTINCT symbol) as stock_count, COUNT(*) as total_records FROM stock_data;

-- 查询某只股票的数据
SELECT * FROM stock_data WHERE symbol='000001' LIMIT 10;

-- 查看同步日志
SELECT * FROM data_sync_log ORDER BY updated_at DESC;

-- 使用 JSONB 查询（适用于 backtest_runs 表）
SELECT id, config->>'strategy_id' as strategy FROM backtest_runs WHERE config->>'commission_rate' = '0.0003';
```

### 4. 数据维护

```bash
# 清理1年前的旧数据
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c \
  "DELETE FROM stock_data WHERE date < CURRENT_DATE - INTERVAL '1 year';"

# 优化数据库（回收空间）
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c "VACUUM FULL stock_data;"

# 重建索引
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c "REINDEX TABLE stock_data;"

# 更新表统计信息
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal -c "ANALYZE stock_data;"
```

### 5. 备份与恢复

```bash
# 备份整个数据库
docker exec stock-backtest-postgres pg_dump -U stockpal stockpal > backup_$(date +%Y%m%d).sql

# 备份单个表
docker exec stock-backtest-postgres pg_dump -U stockpal -t stock_data stockpal > stock_data_backup.sql

# 恢复数据库
docker exec -i stock-backtest-postgres psql -U stockpal stockpal < backup.sql

# 导出为自定义格式（压缩，更快）
docker exec stock-backtest-postgres pg_dump -U stockpal -F c -f /tmp/backup.dump stockpal
docker cp stock-backtest-postgres:/tmp/backup.dump ./backup.dump

# 从自定义格式恢复
docker cp ./backup.dump stock-backtest-postgres:/tmp/backup.dump
docker exec stock-backtest-postgres pg_restore -U stockpal -d stockpal -c /tmp/backup.dump
```

---

## SQL 文件规范

每个模块的 SQL 文件应遵循以下规范：

### 文件命名
- 格式：`{序号}_{模块名}.sql`
- 序号：两位数字（01-99），表示加载顺序
- 示例：`01_stock_data_cache.sql`

### 文件结构
```sql
-- ============================================================================
-- 模块标题 (PostgreSQL)
-- ============================================================================
-- 功能: 模块功能简述
-- 数据库: PostgreSQL 15+
-- 使用: 使用该模块的服务/组件
-- 创建时间: YYYY-MM-DD
-- 最后更新: YYYY-MM-DD
-- 状态: 已实现/设计中/预留
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 表: table_name
-- 说明: 表的用途
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS table_name (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 字段（带注释）
    field_name VARCHAR(50) NOT NULL,  -- 字段说明

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    CONSTRAINT fk_name FOREIGN KEY (field) REFERENCES other_table(id) ON DELETE CASCADE
);

-- 添加表注释
COMMENT ON TABLE table_name IS '表说明';
COMMENT ON COLUMN table_name.field_name IS '字段说明';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_name ON table_name(field_name);

-- 创建触发器（自动更新 updated_at）
CREATE OR REPLACE FUNCTION update_table_name_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_table_name_timestamp
BEFORE UPDATE ON table_name
FOR EACH ROW
EXECUTE FUNCTION update_table_name_timestamp();

-- ----------------------------------------------------------------------------
-- 示例查询
-- ----------------------------------------------------------------------------
-- 示例SQL查询（带注释）

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 维护注意事项
-- 2. 清理策略
-- 3. 性能优化建议
```

### 注释规范
- ✅ 每个表、字段都有清晰注释（使用 COMMENT ON）
- ✅ 提供常用查询示例
- ✅ 说明维护建议
- ✅ 标注状态和依赖
- ✅ 添加触发器实现自动更新时间戳

### PostgreSQL 特性使用
- **SERIAL/BIGSERIAL**: 自增主键
- **NUMERIC**: 精确数值计算（货币、百分比）
- **JSONB**: 结构化JSON数据存储
- **BOOLEAN**: 真正的布尔类型
- **TIMESTAMP**: 高精度时间戳
- **CHECK约束**: 数据验证
- **外键约束**: 数据完整性
- **GIN索引**: JSONB字段加速查询

---

## 数据库配置

### PostgreSQL 配置
```bash
# docker-compose.yml 中的环境变量
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=stockpal
POSTGRES_PASSWORD=stockpal_dev_2024
POSTGRES_DB=stockpal
```

### 连接字符串
```python
# Python
import os
conn_str = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

# 使用 psycopg2
import psycopg2
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'postgres'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER', 'stockpal'),
    password=os.getenv('POSTGRES_PASSWORD', 'stockpal_dev_2024'),
    database=os.getenv('POSTGRES_DB', 'stockpal')
)

# 使用 SQLAlchemy
from sqlalchemy import create_engine
engine = create_engine(conn_str)
```

### Docker 配置
```yaml
# docker-compose.yml 中的 PostgreSQL 服务
postgres:
  image: postgres:15-alpine
  container_name: stock-backtest-postgres
  environment:
    - POSTGRES_USER=stockpal
    - POSTGRES_PASSWORD=stockpal_dev_2024
    - POSTGRES_DB=stockpal
  volumes:
    - postgres-data:/var/lib/postgresql/data
  ports:
    - "5432:5432"
```

---

## 性能优化建议

### 1. 索引优化
- 为常用查询字段创建索引
- 使用 `EXPLAIN ANALYZE` 分析查询
- 为 JSONB 字段创建 GIN 索引
- 定期重建索引（`REINDEX`）

### 2. 查询优化
- 使用 `EXPLAIN ANALYZE` 分析查询计划
- 避免 `SELECT *`，只查询需要的字段
- 使用分页查询（`LIMIT` + `OFFSET`）
- 利用 JSONB 操作符（`->`, `->>`, `@>`）

### 3. 数据清理
- 定期清理过期数据
- 使用 `VACUUM` 回收空间
- 使用 `ANALYZE` 更新统计信息
- 考虑表分区（超大数据量时）

### 4. 监控与调优
```sql
-- 查看慢查询
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- 查看表大小
SELECT
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    pg_size_pretty(pg_relation_size(relid)) as table_size,
    pg_size_pretty(pg_indexes_size(relid)) as indexes_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- 查看索引使用情况
SELECT
    relname as table_name,
    indexrelname as index_name,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## 常见问题

### Q1: 如何连接到 PostgreSQL？
**A**:
```bash
# 从容器内部
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal

# 从宿主机（需安装 psql）
psql -h localhost -p 5432 -U stockpal -d stockpal

# 密码：stockpal_dev_2024
```

### Q2: 如何查看所有表？
**A**:
```sql
-- 在 psql 中
\dt

-- 或使用 SQL
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

### Q3: 如何重置数据库？
**A**:
```bash
# 删除并重新创建数据库
docker exec -it stock-backtest-postgres psql -U stockpal -d postgres -c "DROP DATABASE stockpal;"
docker exec -it stock-backtest-postgres psql -U stockpal -d postgres -c "CREATE DATABASE stockpal;"

# 重新执行初始化脚本
docker exec -it stock-backtest-backend bash -c "cd /app && ./sql/init_db.sh"
```

### Q4: JSONB 字段如何查询？
**A**:
```sql
-- 提取 JSON 字段值
SELECT config->>'strategy_id' as strategy FROM backtest_runs;

-- 查询包含特定值的记录
SELECT * FROM backtest_runs WHERE config->>'commission_rate' = '0.0003';

-- 查询嵌套 JSON
SELECT metrics->'risk'->>'max_drawdown' FROM backtest_runs;

-- 检查 JSON 是否包含键
SELECT * FROM backtest_runs WHERE config ? 'strategy_id';
```

### Q5: 如何查看数据库大小？
**A**:
```sql
-- 数据库总大小
SELECT pg_size_pretty(pg_database_size('stockpal'));

-- 各表大小
SELECT
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

---

## 参考资料

- [PostgreSQL 15 官方文档](https://www.postgresql.org/docs/15/)
- [PostgreSQL 性能优化](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [JSONB 使用指南](https://www.postgresql.org/docs/15/datatype-json.html)
- [psql 命令参考](https://www.postgresql.org/docs/current/app-psql.html)
- [pg_dump 备份工具](https://www.postgresql.org/docs/current/app-pgdump.html)

---

**维护人员**: 开发团队
**最后更新**: 2025-11-16
