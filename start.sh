#!/bin/bash

# Stock Backtest System Startup Script

echo "🚀 启动股票回测系统..."
echo ""

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "📦 创建Python虚拟环境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✅ Python环境配置完成"
    echo ""
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd frontend
    npm install
    cd ..
    echo "✅ 前端依赖安装完成"
    echo ""
fi

# Start backend
echo "🔧 启动后端服务..."
cd backend
source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
echo "   访问: http://localhost:5000"
echo ""

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
echo "   访问: http://localhost:5173"
echo ""

echo "🎉 系统启动完成！"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
