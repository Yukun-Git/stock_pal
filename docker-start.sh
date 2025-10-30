#!/bin/bash

# Docker Quick Start Script for Stock Backtest System
# This script provides a simple way to start the system using Docker

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  📈 股票回测系统 - Docker 启动${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
        exit 1
    fi
    print_success "Docker 已安装"
}

check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装"
        echo "请访问 https://docs.docker.com/compose/install/ 安装 Docker Compose"
        exit 1
    fi
    print_success "Docker Compose 已安装"
}

check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行"
        print_info "请启动 Docker Desktop（macOS/Windows）或 Docker 服务（Linux）"
        exit 1
    fi
    print_success "Docker 服务正在运行"
}

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_warning "端口 $port 已被占用"
        echo "请停止占用该端口的程序，或修改 docker-compose.yml 中的端口配置"
        return 1
    fi
    return 0
}

# Main script
print_header

print_info "步骤 1/5: 检查环境..."
check_docker
check_docker_compose
check_docker_running

print_info "\n步骤 2/5: 检查端口占用..."
port_check_failed=0
if ! check_port 80; then
    port_check_failed=1
fi
if ! check_port 5000; then
    port_check_failed=1
fi

if [ $port_check_failed -eq 1 ]; then
    echo ""
    read -p "是否继续启动？部分服务可能无法访问 (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "已取消启动"
        exit 0
    fi
fi

print_success "端口检查完成"

print_info "\n步骤 3/5: 构建 Docker 镜像..."
print_warning "首次构建可能需要 5-10 分钟，请耐心等待..."
if docker-compose build; then
    print_success "镜像构建完成"
else
    print_error "镜像构建失败，请查看上方错误信息"
    exit 1
fi

print_info "\n步骤 4/5: 启动服务..."
if docker-compose up -d; then
    print_success "服务启动完成"
else
    print_error "服务启动失败，请查看上方错误信息"
    exit 1
fi

print_info "\n步骤 5/5: 等待服务就绪..."
sleep 3

# Check service health
backend_healthy=0
frontend_healthy=0

for i in {1..30}; do
    if docker-compose ps | grep -q "stock-backtest-backend.*healthy"; then
        backend_healthy=1
    fi
    if docker-compose ps | grep -q "stock-backtest-frontend.*Up"; then
        frontend_healthy=1
    fi

    if [ $backend_healthy -eq 1 ] && [ $frontend_healthy -eq 1 ]; then
        break
    fi

    echo -n "."
    sleep 2
done

echo ""

if [ $backend_healthy -eq 1 ]; then
    print_success "后端服务就绪"
else
    print_warning "后端服务可能未完全就绪，请稍后再试"
fi

if [ $frontend_healthy -eq 1 ]; then
    print_success "前端服务就绪"
else
    print_warning "前端服务可能未完全就绪，请稍后再试"
fi

# Print summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  🎉 启动成功！${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "访问地址: ${BLUE}http://localhost${NC}"
echo -e "后端API:  ${BLUE}http://localhost:5000${NC}"
echo ""
echo "常用命令:"
echo "  • 查看日志:   ${BLUE}docker-compose logs -f${NC}"
echo "  • 查看状态:   ${BLUE}docker-compose ps${NC}"
echo "  • 停止服务:   ${BLUE}docker-compose down${NC}"
echo "  • 重启服务:   ${BLUE}docker-compose restart${NC}"
echo ""
echo "更多命令请查看: ${BLUE}make help${NC} 或 ${BLUE}DOCKER_DEPLOYMENT.md${NC}"
echo ""

# Open browser (optional)
read -p "是否在浏览器中打开？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open http://localhost
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open http://localhost 2>/dev/null || echo "请手动打开浏览器访问 http://localhost"
    else
        # Windows (Git Bash)
        start http://localhost 2>/dev/null || echo "请手动打开浏览器访问 http://localhost"
    fi
fi

print_info "\n祝您使用愉快！📈"
