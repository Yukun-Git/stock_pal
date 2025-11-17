#!/bin/bash
# ============================================================================
# Stock Pal 数据库初始化脚本 (PostgreSQL)
# ============================================================================
# 功能: 初始化PostgreSQL数据库，创建所有表结构
# 使用: ./sql/init_db.sh
# 要求: PostgreSQL 15+ Docker 容器运行中
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 数据库连接配置（从环境变量或使用默认值）
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-stockpal}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-stockpal_dev_2024}"
POSTGRES_DB="${POSTGRES_DB:-stockpal}"

SQL_DIR="sql/modules"

echo "========================================"
echo "  Stock Pal 数据库初始化 (PostgreSQL)"
echo "========================================"
echo ""

# 显示连接信息
echo -e "${BLUE}数据库连接信息:${NC}"
echo "  主机: $POSTGRES_HOST"
echo "  端口: $POSTGRES_PORT"
echo "  用户: $POSTGRES_USER"
echo "  数据库: $POSTGRES_DB"
echo ""

# 检查 psql 命令是否可用
if ! command -v psql &> /dev/null; then
    echo -e "${RED}错误: psql 命令未找到${NC}"
    echo "请确保 PostgreSQL 客户端已安装"
    exit 1
fi

# 检查 SQL 模块目录
if [ ! -d "$SQL_DIR" ]; then
    echo -e "${RED}错误: SQL 模块目录不存在: $SQL_DIR${NC}"
    exit 1
fi

# 检查是否有 SQL 文件
SQL_FILES=$(ls $SQL_DIR/*.sql 2>/dev/null | sort)
if [ -z "$SQL_FILES" ]; then
    echo -e "${RED}错误: 未找到任何 SQL 文件在 $SQL_DIR${NC}"
    exit 1
fi

# 设置 PGPASSWORD 环境变量以避免密码提示
export PGPASSWORD="$POSTGRES_PASSWORD"

# 建立数据库连接测试
echo -e "${BLUE}测试数据库连接...${NC}"
if ! psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}错误: 无法连接到 PostgreSQL 服务器${NC}"
    echo "请检查:"
    echo "  1. PostgreSQL 服务是否运行"
    echo "  2. 连接信息是否正确 (主机: $POSTGRES_HOST, 端口: $POSTGRES_PORT)"
    echo "  3. 用户凭证是否正确"
    exit 1
fi
echo -e "${GREEN}连接成功${NC}"
echo ""

# 检查数据库是否存在
echo -e "${BLUE}检查数据库状态...${NC}"
DB_EXISTS=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB';" 2>/dev/null)

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}警告: 数据库已存在: $POSTGRES_DB${NC}"
    read -p "是否重新初始化数据库? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}取消初始化${NC}"
        exit 0
    fi

    # 删除现有数据库
    echo -e "${GREEN}删除现有数据库...${NC}"
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" > /dev/null 2>&1
fi

# 创建数据库
echo -e "${GREEN}创建新数据库: $POSTGRES_DB${NC}"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -c "CREATE DATABASE $POSTGRES_DB ENCODING 'UTF8';" > /dev/null 2>&1

echo -e "${GREEN}数据库创建成功${NC}"
echo ""

# 执行 SQL 模块
echo "开始执行 SQL 模块..."
echo ""

for sql_file in $SQL_FILES; do
    module_name=$(basename "$sql_file")
    echo -e "${GREEN}[执行] $module_name${NC}"

    if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$sql_file" > /dev/null 2>&1; then
        echo -e "${GREEN}[成功] $module_name${NC}"
    else
        echo -e "${RED}[失败] $module_name${NC}"
        echo "执行以下命令查看详细错误:"
        echo "  psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -f $sql_file"
        exit 1
    fi
    echo ""
done

# 应用 PostgreSQL 优化配置
echo -e "${GREEN}应用 PostgreSQL 优化配置...${NC}"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF' > /dev/null 2>&1
-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 设置默认字符编码
ALTER DATABASE stockpal SET client_encoding = 'UTF8';
EOF

echo -e "${GREEN}优化配置应用完成${NC}"
echo ""

# 验证表结构
echo "========================================"
echo "  数据库表结构验证"
echo "========================================"
echo ""

TABLE_COUNT=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
echo -e "已创建表数量: ${GREEN}$TABLE_COUNT${NC}"
echo ""

# 显示所有表
echo "数据库表列表:"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt" | head -20

echo ""
echo "========================================"
echo "  初始化完成"
echo "========================================"
echo -e "${GREEN}PostgreSQL 数据库初始化成功!${NC}"
echo ""
echo "数据库详情:"
echo -e "  数据库名: ${GREEN}$POSTGRES_DB${NC}"
echo -e "  连接字符串: ${GREEN}postgresql://$POSTGRES_USER:****@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB${NC}"
echo ""
echo "可以使用以下命令连接数据库:"
echo "  psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB"
echo ""

# 清理环境变量
unset PGPASSWORD

echo -e "${GREEN}操作完成${NC}"
