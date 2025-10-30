# 📈 股票回测系统 (Stock Backtest System)

一个为散户投资者设计的股票交易策略回测系统，帮助验证交易理论，提升交易胜率。

## ✨ 功能特性

- 🔍 **股票搜索**：支持通过代码或名称快速搜索A股股票
- 📊 **技术指标**：内置MA、EMA、MACD、KDJ、RSI、布林带等常用技术指标
- 🎯 **预设策略**：提供早晨之星、MACD金叉、均线交叉等经典交易策略
- 📈 **数据可视化**：K线图、买卖点标注、资产曲线、交易明细
- 💰 **回测分析**：收益率、胜率、最大回撤、盈利因子等核心指标
- 🎨 **现代UI**：基于Ant Design，界面简洁美观

## 🛠️ 技术栈

### 后端
- **框架**：Flask 3.0 + Flask-RESTful
- **数据源**：AkShare（免费A股数据）
- **数据处理**：Pandas + NumPy
- **技术指标**：pandas-ta

### 前端
- **框架**：React 18 + TypeScript
- **UI库**：Ant Design 5
- **图表**：ECharts 5
- **构建工具**：Vite

## 📦 项目结构

```
stock/
├── backend/                 # Flask后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   │   └── v1/
│   │   │       ├── stocks.py      # 股票相关API
│   │   │       └── backtest.py    # 回测相关API
│   │   ├── services/       # 业务逻辑
│   │   │   ├── data_service.py      # 数据获取服务
│   │   │   ├── indicator_service.py # 技术指标计算
│   │   │   ├── strategy_service.py  # 策略定义
│   │   │   └── backtest_service.py  # 回测引擎
│   │   ├── models/         # 数据模型
│   │   └── utils/          # 工具函数
│   ├── requirements.txt
│   └── run.py
│
├── frontend/               # React前端
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   │   ├── HomePage.tsx
│   │   │   └── BacktestPage.tsx
│   │   ├── components/    # 通用组件
│   │   │   ├── KLineChart.tsx
│   │   │   └── EquityCurveChart.tsx
│   │   ├── services/      # API调用
│   │   │   └── api.ts
│   │   ├── types/         # TypeScript类型
│   │   └── utils/         # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
└── 散户常用技术指标与交易方法论.md  # 技术文档
```

## 🚀 快速开始

有两种部署方式可供选择：

### 🐳 方式一：Docker 部署（**强烈推荐**）

**适合场景**：快速部署、生产环境、无需配置开发环境

**环境要求**：
- Docker 20.10+
- Docker Compose 2.0+

**启动步骤**：

```bash
# 1. 进入项目目录
cd /Users/yukun-admin/projects/stock

# 2. 一键启动（自动构建镜像并启动服务）
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 访问系统 - 打开浏览器访问
http://localhost
```

**常用命令**：

```bash
# 查看实时日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重新构建并启动
docker-compose up -d --build
```

**使用 Makefile（更便捷）**：

```bash
make help      # 查看所有可用命令
make up        # 启动服务
make logs      # 查看日志
make down      # 停止服务
make rebuild   # 重新构建
```

> 📖 **详细文档**：查看 [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) 了解更多 Docker 部署细节、故障排查和生产环境配置

---

### 💻 方式二：本地开发部署

**适合场景**：开发调试、代码修改、学习研究

**环境要求**：
- Python 3.8+
- Node.js 16+
- npm 或 yarn

#### 1. 后端安装与启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp .env.example .env

# 启动后端服务
python run.py
```

后端服务将运行在 `http://localhost:5000`

#### 2. 前端安装与启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将运行在 `http://localhost:5173`

#### 3. 访问系统

打开浏览器访问：`http://localhost:5173`

## 📖 使用说明

### 1. 选择股票
- 在回测页面的"股票代码/名称"输入框中输入关键字
- 系统会自动搜索匹配的股票
- 选择您想要回测的股票

### 2. 选择策略
系统内置以下交易策略：

- **早晨之星**：底部反转形态，三根K线组合，看涨信号
- **均线金叉**：短期均线上穿长期均线买入，下穿卖出
- **MACD金叉**：DIF上穿DEA买入，下穿卖出
- **KDJ金叉**：K线上穿D线且在低位(<30)买入，高位(>70)卖出
- **RSI反转**：RSI < 30超卖买入，RSI > 70超买卖出
- **布林带突破**：价格突破下轨买入，突破上轨卖出

### 3. 设置参数
- **回测时间区间**：选择要回测的起止日期（默认最近2年）
- **初始资金**：设置初始投资金额（默认10万元）
- **手续费率**：设置交易手续费率（默认0.03%）

### 4. 查看结果
回测完成后，系统将展示：
- **核心指标**：总收益率、胜率、最大回撤等
- **K线图**：带买卖点标注的K线图
- **资产曲线**：资产变化趋势图
- **交易明细**：每笔交易的详细记录

## 🎯 支持的技术指标

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

## 🔧 开发命令

### 后端
```bash
# 运行后端
python run.py

# 代码格式化
black app/

# 代码检查
flake8 app/
```

### 前端
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

## 📝 API接口文档

### 股票相关

#### 搜索股票
```
GET /api/v1/stocks/search?keyword={keyword}
```

#### 获取股票数据
```
GET /api/v1/stocks/{symbol}/data?start_date={date}&end_date={date}
```

### 回测相关

#### 获取策略列表
```
GET /api/v1/strategies
```

#### 运行回测
```
POST /api/v1/backtest
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

## 🐛 常见问题

### 1. 后端启动失败
- 检查Python版本是否 >= 3.8
- 检查是否所有依赖都已安装：`pip install -r requirements.txt`
- 检查5000端口是否被占用

### 2. 前端无法连接后端
- 确保后端服务已启动（http://localhost:5000）
- 检查前端 `.env.development` 中的 `VITE_API_BASE_URL` 配置
- 检查浏览器控制台是否有CORS错误

### 3. 获取股票数据失败
- 检查网络连接
- AkShare可能需要一些时间来获取数据
- 某些股票代码可能不存在或已退市

### 4. 回测计算时间过长
- 回测2年以上的数据可能需要几秒到几十秒
- 可以缩短回测时间区间
- 未来可以考虑添加缓存机制

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

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**：本系统仅用于学习和研究目的，回测结果不代表实际交易收益，投资有风险，入市需谨慎！
