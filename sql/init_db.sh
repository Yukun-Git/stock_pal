#!/bin/bash
# ============================================================================
# Stock Pal 数据库初始化脚本
# ============================================================================
# 功能: 初始化SQLite数据库，创建所有表结构
# 使用: ./sql/init_db.sh [database_path]
# ============================================================================

set -e  # 遇到错误立即退出

# 配置
DEFAULT_DB_PATH="data/stock_cache.db"
DB_PATH="${1:-$DEFAULT_DB_PATH}"
SQL_DIR="sql/modules"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Stock Pal 数据库初始化"
echo "========================================"
echo ""

# 检查数据库文件是否存在
if [ -f "$DB_PATH" ]; then
    echo -e "${YELLOW}警告: 数据库文件已存在: $DB_PATH${NC}"
    read -p "是否备份并重新初始化? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_PATH="${DB_PATH}.backup_$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}备份到: $BACKUP_PATH${NC}"
        cp "$DB_PATH" "$BACKUP_PATH"
        rm "$DB_PATH"
    else
        echo -e "${YELLOW}取消初始化${NC}"
        exit 0
    fi
fi

# 创建数据目录
DB_DIR=$(dirname "$DB_PATH")
if [ ! -d "$DB_DIR" ]; then
    echo -e "${GREEN}创建数据目录: $DB_DIR${NC}"
    mkdir -p "$DB_DIR"
fi

# 执行SQL模块
echo ""
echo "开始执行SQL模块..."
echo ""

for sql_file in $(ls $SQL_DIR/*.sql | sort); do
    module_name=$(basename "$sql_file")
    echo -e "${GREEN}[执行] $module_name${NC}"

    if sqlite3 "$DB_PATH" < "$sql_file"; then
        echo -e "${GREEN}[成功] $module_name${NC}"
    else
        echo -e "${RED}[失败] $module_name${NC}"
        exit 1
    fi
    echo ""
done

# 设置SQLite优化选项
echo -e "${GREEN}应用SQLite优化配置...${NC}"
sqlite3 "$DB_PATH" <<EOF
-- 启用WAL模式（提升并发性能）
PRAGMA journal_mode=WAL;

-- 设置同步模式
PRAGMA synchronous=NORMAL;

-- 启用外键约束
PRAGMA foreign_keys=ON;

-- 设置缓存大小（2MB）
PRAGMA cache_size=-2000;

-- 设置超时时间（5秒）
PRAGMA busy_timeout=5000;
EOF

# 验证表结构
echo ""
echo "========================================"
echo "  数据库表结构"
echo "========================================"
sqlite3 "$DB_PATH" ".tables"

# 统计信息
echo ""
echo "========================================"
echo "  初始化完成"
echo "========================================"
echo -e "${GREEN}数据库路径: $DB_PATH${NC}"
echo -e "${GREEN}文件大小: $(du -h "$DB_PATH" | cut -f1)${NC}"
echo ""

# 显示表数量
TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
echo -e "已创建表数量: ${GREEN}$TABLE_COUNT${NC}"

echo ""
echo "可以使用以下命令查看数据库:"
echo "  sqlite3 $DB_PATH"
echo ""
