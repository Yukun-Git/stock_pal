# 📈 Stock_Pal - 股票回测系统 项目指南

## 📋 项目概述

Stock_Pal 是一个为散户投资者设计的股票交易策略回测系统，旨在帮助用户验证交易理论并提升交易胜率。系统提供多种技术指标、预设交易策略以及可视化回测结果分析。

对于重新构建镜像一定要谨慎，太费时间。大部分时候，能够通过重启服务就能达到目的。
所有的端口设置一定要小心，绝不能和宿主机上的其他服务产生冲突（PORT_INFO.md）。
写详细设计文档的时候，不要包含具体的代码实现，以免文档过长。
目前项目处于早期阶段，所有的详细设计和开发计划都不需要考虑数据迁移之类的内容。
如果想创建一些临时性的脚本，用于做一些测试，先去看看backend/debug_scripts目录下有没有现成的。如果没有，新创建的测试脚本也要放到backend/debug_scripts目录下。

### 核心功能
- **股票搜索**：支持通过代码或名称快速搜索A股股票
- **技术指标**：内置MA、EMA、MACD、KDJ、RSI、布林带等常用技术指标
- **预设策略**：提供早晨之星、MACD金叉、均线交叉等经典交易策略
- **数据可视化**：K线图、买卖点标注、资产曲线、交易明细
- **回测分析**：收益率、胜率、最大回撤、盈利因子等核心指标
- **现代UI**：基于Ant Design，界面简洁美观

### 技术栈
- **后端**：Flask 3.0 + Flask-RESTful, PostgreSQL, Pandas, NumPy
- **前端**：React 18 + TypeScript, Ant Design 5, ECharts 5
- **数据源**：AkShare（免费A股数据）和 Yahoo Finance
- **数据库**：PostgreSQL
- **构建工具**：Vite

## 🏗️ 项目结构

```
stock_pal/
├── backend/                 # Flask后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── backtest/       # 回测引擎
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   ├── strategies/     # 交易策略
│   │   └── utils/          # 工具函数
│   ├── requirements.txt    # Python依赖
│   └── run.py              # 启动文件
├── frontend/               # React前端
│   ├── src/
│   │   ├── components/     # 通用组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API调用
│   │   ├── types/          # TypeScript类型
│   │   └── utils/          # 工具函数
│   ├── package.json        # Node.js依赖
│   └── vite.config.ts      # 构建配置
├── docker-compose.yml      # Docker容器配置
├── Makefile                # 构建命令
├── README.md               # 详细文档
└── PORT_INFO.md            # 端口配置文档
```

## 🔧 端口分配

- **前端开发**：`4000` (http://localhost:4000)
- **后端API**：`4001` (http://localhost:4001)
- **Docker前端**：`4080` (http://localhost:4080)
- **PostgreSQL**：`5432` (localhost:5432)

## 🚀 部署选项

### 1. Docker 部署（推荐）

**启动命令：**
```bash
# 使用Makefile（推荐）
make up

# 或直接使用docker-compose
docker-compose up -d

# 检查服务状态
make ps
```

**Docker相关命令：**
- `make logs` - 查看实时日志
- `make down` - 停止所有服务
- `make rebuild` - 重新构建并启动
- `make restart` - 重启所有服务

### 2. 本地开发部署

**后端启动：**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**前端启动：**
```bash
cd frontend
npm install
npm run dev
```

### 3. 使用启动脚本
```bash
chmod +x start.sh
./start.sh
```

## 📊 API接口文档

### 股票相关
- `GET /api/v1/stocks/search?keyword={keyword}` - 搜索股票
- `GET /api/v1/stocks/{symbol}/data?start_date={date}&end_date={date}` - 获取股票数据

### 回测相关
- `GET /api/v1/strategies` - 获取策略列表
- `POST /api/v1/backtest` - 运行回测

**回测请求示例：**
```json
{
  "symbol": "000001",
  "strategy_id": "ma_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "initial_capital": 100000,
  "commission_rate": 0.0003,
  "strategy_params": {}
}
```

## 🧪 开发与测试命令

### 后端开发命令
```bash
# 运行后端
python run.py

# 代码格式化
black app/

# 代码检查
flake8 app/

# 运行测试
pytest

# Docker容器中运行测试
make test-backend
make lint-backend
make format-backend
```

### 前端开发命令
```bash
# 开发模式
npm run dev

# 生产构建
npm run build

# 代码检查
npm run lint

# 预览构建结果
npm run preview
```

### Docker容器访问
```bash
# 访问后端容器
make shell-backend

# 访问前端容器
make shell-frontend

# 访问PostgreSQL数据库
docker exec -it stock-backtest-postgres psql -U stockpal -d stockpal
```

## ⚙️ 配置文件

### 环境变量
后端使用 `.env` 文件配置：
- `FLASK_ENV`: 环境类型 (development/production)
- `DATA_SOURCE`: 数据源 (akshare/yfinance)
- `POSTGRES_HOST`: PostgreSQL主机
- `POSTGRES_PORT`: PostgreSQL端口
- `POSTGRES_USER`: PostgreSQL用户名
- `POSTGRES_PASSWORD`: PostgreSQL密码
- `POSTGRES_DB`: PostgreSQL数据库名

### 前端环境变量
- `VITE_API_BASE_URL`: API基础URL

## 📈 支持的技术指标

| 指标类型 | 包含指标 |
|---------|---------|
| **趋势类** | MA（移动平均）、EMA（指数移动平均） |
| **动量类** | MACD、KDJ、RSI |
| **波动类** | 布林带（BOLL） |
| **形态识别** | 早晨之星、黄昏之星 |

## 📊 回测指标说明

| 指标 | 说明 |
|-----|------|
| **总收益率** | (最终资金 - 初始资金) / 初始资金 × 100% |
| **交易次数** | 总共完成的买卖交易对数 |
| **胜率** | 盈利交易次数 / 总交易次数 × 100% |
| **最大回撤** | 资产净值从最高点到最低点的最大跌幅 |
| **盈利因子** | 总盈利 / 总亏损（越大越好，>1表示盈利） |
| **平均盈利** | 盈利交易的平均盈利金额 |
| **平均亏损** | 亏损交易的平均亏损金额 |

## 🔧 开发约定

### 命名约定
- Python文件使用下划线命名法：`data_service.py`
- React组件使用帕斯卡命名法：`KLineChart.tsx`
- API端点使用名词复数形式：`/api/v1/stocks`

### 代码结构
- 后端代码遵循MVC模式，分离模型、视图和控制器
- 前端采用组件化架构，页面组件负责业务逻辑，通用组件负责UI展示
- API版本控制使用URL路径（v1）

### 测试约定
- 单元测试位于 `backend/tests/` 目录中
- 测试文件以 `test_` 为前缀
- 使用pytest框架进行测试

## 🐛 故障排除

### 常见问题

1. **后端启动失败**
   - 检查Python版本是否 >= 3.8
   - 检查依赖是否安装完整：`pip install -r requirements.txt`
   - 检查端口是否被占用：`lsof -i :4001`

2. **前端无法连接后端**
   - 确保后端服务已启动（http://localhost:4001）
   - 检查前端 `.env.development` 中的 `VITE_API_BASE_URL` 配置
   - 检查CORS配置

3. **获取股票数据失败**
   - 检查网络连接
   - AkShare可能不稳定，可切换到yfinance数据源

4. **回测计算时间过长**
   - 回测历史数据可能需要几秒到几十秒
   - 可以缩短回测时间区间
   - 考虑使用缓存机制

### Docker相关问题

- 检查Docker服务是否运行：`docker ps`
- 查看服务日志：`make logs`
- 重新构建镜像：`make rebuild`
- 清理所有容器：`make clean-all`

## 🚧 后续计划

- [ ] 添加更多预设策略（双均线、三均线、MACD+KDJ组合等）
- [ ] 支持自定义策略（可视化规则编辑器）
- [ ] 支持自然语言描述策略
- [ ] 参数优化功能（寻找最优参数组合）
- [ ] 多股票批量回测
- [ ] 回测结果对比功能
- [ ] 支持周K、月K等不同周期
- [ ] 数据缓存机制
- [ ] 用户账户系统（保存策略和回测历史）

## 📄 许可证

MIT License