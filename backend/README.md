# Backend - 股票回测系统后端

基于Flask的股票回测系统后端API服务。

## 技术栈

- Flask 3.0
- Flask-RESTful
- AkShare (股票数据源)
- Pandas & NumPy (数据处理)
- pandas-ta (技术指标计算)

## 安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
```

## 运行

```bash
# 开发模式
python run.py

# 生产模式
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## API端点

### 健康检查
```
GET /health
```

### 股票API
```
GET /api/v1/stocks              # 获取股票列表
GET /api/v1/stocks/search       # 搜索股票
GET /api/v1/stocks/{symbol}/data # 获取股票数据
```

### 策略API
```
GET /api/v1/strategies          # 获取策略列表
```

### 回测API
```
POST /api/v1/backtest          # 运行回测
```

## 项目结构

```
backend/
├── app/
│   ├── __init__.py           # Flask应用工厂
│   ├── config.py             # 配置文件
│   ├── api/                  # API路由
│   │   └── v1/
│   │       ├── stocks.py     # 股票相关API
│   │       └── backtest.py   # 回测相关API
│   ├── services/             # 业务逻辑层
│   │   ├── data_service.py      # 数据获取
│   │   ├── indicator_service.py # 指标计算
│   │   ├── strategy_service.py  # 策略定义
│   │   └── backtest_service.py  # 回测引擎
│   ├── models/               # 数据模型
│   └── utils/                # 工具函数
├── requirements.txt
└── run.py
```

## 添加新策略

在 `app/services/strategy_service.py` 中使用装饰器注册新策略：

```python
@StrategyService.register_strategy(
    name='my_strategy',
    description='我的自定义策略'
)
def my_strategy(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    df['signal'] = 0

    # 实现你的策略逻辑
    # df.loc[条件, 'signal'] = 1  # 买入信号
    # df.loc[条件, 'signal'] = -1 # 卖出信号

    return df
```
