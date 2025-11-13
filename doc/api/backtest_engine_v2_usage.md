# 回测引擎 2.0 API 使用指南

本文档展示如何使用升级后的回测引擎进行回测、参数优化和走步验证。

## 目录

1. [基础回测](#基础回测)
2. [参数优化](#参数优化)
3. [走步验证](#走步验证)
4. [集成到现有API](#集成到现有api)

---

## 基础回测

### 使用 BacktestOrchestrator

```python
from app.backtest.orchestrator import BacktestOrchestrator
from app.backtest.models import BacktestConfig
import pandas as pd

# 1. 创建回测配置
config = BacktestConfig(
    symbol='600000',
    start_date='20230101',
    end_date='20231231',
    initial_capital=100000,
    commission_rate=0.0003,
    min_commission=5.0,
    slippage_bps=5.0,
    stamp_tax_rate=0.001
)

# 2. 准备市场数据（OHLCV）
market_data = pd.DataFrame({
    'date': pd.date_range('2023-01-01', '2023-12-31', freq='B'),
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...],
    'prev_close': [...]
})

# 3. 准备交易信号
signals = pd.DataFrame({
    'date': market_data['date'],
    'signal': [...]  # 1=买入, -1=卖出, 0=持有
})

# 4. 运行回测
orchestrator = BacktestOrchestrator(config)
result = orchestrator.run(market_data, signals)

# 5. 获取结果
print(f"总收益: {result.metrics['total_return']:.2%}")
print(f"Sharpe比率: {result.metrics['sharpe_ratio']:.2f}")
print(f"最大回撤: {result.metrics['max_drawdown']:.2%}")
print(f"交易次数: {len(result.trades)}")

# 6. 权益曲线
equity_curve = result.equity_curve
# DataFrame with columns: date, equity, cash, position_value
```

### 使用策略函数

```python
# 定义策略函数
def ma_cross_strategy(data, params):
    """均线交叉策略"""
    df = data.copy()

    # 计算均线
    short_period = params['short_period']
    long_period = params['long_period']
    df['ma_short'] = df['close'].rolling(window=short_period).mean()
    df['ma_long'] = df['close'].rolling(window=long_period).mean()

    # 生成信号
    df['signal'] = 0
    df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
    df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1

    # 去重（只保留信号变化）
    df['signal_change'] = df['signal'].diff()
    df.loc[df['signal_change'] == 0, 'signal'] = 0

    return df[['date', 'signal']]

# 使用策略函数运行回测
result = orchestrator.run_with_strategy(
    market_data,
    ma_cross_strategy,
    strategy_params={'short_period': 10, 'long_period': 60}
)
```

---

## 参数优化

### 网格搜索

```python
from app.backtest.optimization import GridSearchOptimizer

# 1. 创建优化器
param_grid = {
    'short_period': [5, 10, 15, 20],
    'long_period': [30, 60, 90, 120]
}

optimizer = GridSearchOptimizer(
    config=config,
    param_grid=param_grid,
    optimization_metric='sharpe_ratio'  # 或 'calmar_ratio', 'total_return'
)

# 2. 运行优化
result = optimizer.optimize(
    market_data,
    ma_cross_strategy
)

# 3. 获取最佳参数
print(f"最佳参数: {result.best_params}")
print(f"最佳得分: {result.best_score:.4f}")
print(f"测试组合数: {result.total_combinations}")
print(f"执行时间: {result.execution_time_seconds:.2f}秒")

# 4. 查看所有结果
for item in result.all_results:
    print(f"参数: {item['params']}, "
          f"Sharpe: {item['score']:.2f}, "
          f"收益: {item['total_return']:.2%}")

# 5. 热力图数据（用于前端可视化）
if result.heatmap_data:
    heatmap = result.heatmap_data
    # {
    #   'x_param': 'short_period',
    #   'x_values': [5, 10, 15, 20],
    #   'y_param': 'long_period',
    #   'y_values': [30, 60, 90, 120],
    #   'z_values': [[...], [...], ...]  # Sharpe ratio matrix
    # }
```

### 带约束的优化

```python
# 添加约束条件
constraints = {
    'min_sharpe_ratio': 1.0,  # Sharpe比率至少1.0
    'max_max_drawdown': -0.20  # 最大回撤不超过-20%
}

result = optimizer.optimize(
    market_data,
    ma_cross_strategy,
    constraints=constraints
)
```

---

## 走步验证

### 防止过拟合

```python
from app.backtest.optimization import WalkForwardValidator

# 1. 创建验证器
validator = WalkForwardValidator(
    config=config,
    train_period_months=12,  # 训练期12个月
    test_period_months=3,    # 测试期3个月
    step_months=3,           # 每次步进3个月
    optimization_metric='sharpe_ratio'
)

# 2. 运行走步验证
result = validator.validate(
    market_data,
    ma_cross_strategy,
    param_grid=param_grid,
    optimize_in_train=True  # 在训练期优化参数
)

# 3. 查看整体结果
print(f"验证周期数: {result.total_periods}")
print(f"平均训练期Sharpe: {result.overall_metrics['avg_train_sharpe']:.2f}")
print(f"平均测试期Sharpe: {result.overall_metrics['avg_test_sharpe']:.2f}")
print(f"平均衰减: {result.overall_metrics['avg_degradation']:.2%}")
print(f"是否过拟合: {result.is_overfitting}")

# 4. 查看每个周期
for period in result.periods:
    print(f"\n周期 {period.period_id}:")
    print(f"  训练期: {period.train_start} ~ {period.train_end}")
    print(f"  测试期: {period.test_start} ~ {period.test_end}")
    print(f"  最优参数: {period.train_best_params}")
    print(f"  训练期Sharpe: {period.train_metrics['sharpe_ratio']:.2f}")
    print(f"  测试期Sharpe: {period.test_metrics['sharpe_ratio']:.2f}")
    print(f"  衰减: {period.get_degradation('sharpe_ratio'):.2%}")
```

---

## 集成到现有API

### 扩展 `/api/v1/backtest` 端点

```python
# backend/app/api/v1/backtest.py

from flask import request, jsonify
from app.backtest.orchestrator import BacktestOrchestrator
from app.backtest.models import BacktestConfig
from app.services.data_service import DataService
from app.services.strategy_service import StrategyService

@bp.route('/backtest', methods=['POST'])
def run_backtest():
    """运行回测"""
    data = request.json

    # 1. 获取市场数据
    market_data = DataService.get_stock_data(
        symbol=data['symbol'],
        start_date=data['start_date'],
        end_date=data['end_date']
    )

    # 2. 创建配置
    config = BacktestConfig(
        symbol=data['symbol'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        initial_capital=data.get('initial_capital', 100000),
        commission_rate=data.get('commission_rate', 0.0003),
        min_commission=data.get('min_commission', 5.0),
        slippage_bps=data.get('slippage_bps', 5.0),
        stamp_tax_rate=data.get('stamp_tax_rate', 0.001)
    )

    # 3. 获取策略函数
    strategy_func = StrategyService.get_strategy(data['strategy_id'])
    strategy_params = data.get('strategy_params', {})

    # 4. 运行回测
    orchestrator = BacktestOrchestrator(config)
    result = orchestrator.run_with_strategy(
        market_data,
        strategy_func,
        strategy_params
    )

    # 5. 返回结果
    return jsonify({
        'success': True,
        'data': {
            'backtest_id': result.metadata['backtest_id'],
            'metrics': result.metrics,
            'trades': [
                {
                    'date': t.executed_at.isoformat(),
                    'side': t.side.value,
                    'quantity': t.quantity,
                    'price': t.price,
                    'amount': t.amount,
                    'commission': t.commission
                }
                for t in result.trades
            ],
            'equity_curve': result.equity_curve.to_dict('records'),
            'metadata': result.metadata
        }
    })
```

### 添加优化端点

```python
@bp.route('/backtest/optimize', methods=['POST'])
def optimize_parameters():
    """参数优化"""
    data = request.json

    # 获取数据和策略
    market_data = DataService.get_stock_data(...)
    strategy_func = StrategyService.get_strategy(data['strategy_id'])

    # 创建优化器
    from app.backtest.optimization import GridSearchOptimizer

    optimizer = GridSearchOptimizer(
        config=config,
        param_grid=data['param_grid'],
        optimization_metric=data.get('optimization_metric', 'sharpe_ratio')
    )

    # 运行优化
    result = optimizer.optimize(
        market_data,
        strategy_func,
        constraints=data.get('constraints')
    )

    # 返回结果
    return jsonify({
        'success': True,
        'data': {
            'best_params': result.best_params,
            'best_score': result.best_score,
            'all_results': result.all_results[:100],  # 限制返回数量
            'heatmap_data': result.heatmap_data,
            'execution_time': result.execution_time_seconds
        }
    })
```

---

## 性能指标说明

新引擎计算的所有指标：

### 收益指标
- `total_return`: 总收益（绝对值）
- `cagr`: 复合年化增长率
- `annual_return`: 年化收益率

### 风险指标
- `volatility`: 波动率（年化）
- `max_drawdown`: 最大回撤
- `max_drawdown_duration`: 最大回撤持续期（天数）

### 风险调整收益
- `sharpe_ratio`: Sharpe比率
- `sortino_ratio`: Sortino比率
- `calmar_ratio`: Calmar比率

### 交易统计
- `total_trades`: 总交易次数
- `win_rate`: 胜率
- `profit_factor`: 盈亏比
- `avg_trade_return`: 平均交易收益率

### 持仓统计
- `turnover_rate`: 换手率（年化）
- `avg_holding_period`: 平均持仓天数

---

## 注意事项

1. **交易规则**: 新引擎自动应用T+1、涨跌停、停牌等规则
2. **板块识别**: 根据股票代码自动识别板块（主板/创业板/科创板）
3. **元数据**: 每次回测都会生成唯一ID和完整元数据，支持可复现性
4. **性能**: 单次回测（2年数据）约1-2秒，参数优化视组合数而定
5. **并行化**: 未来可扩展多进程并行优化

---

## 示例代码

完整示例见：`backend/tests/backtest/test_orchestrator.py` 和 `test_optimization.py`
