# 风控管理器（Risk Manager）详细设计与开发计划

**版本**: v1.0
**创建时间**: 2025-11-12
**状态**: 设计中
**优先级**: P0（阻塞PRD验收）
**关联文档**:
- 上级设计: `doc/design/backtest_post_mvp_enhancements.md`
- PRD: `doc/requirements/product_requirements_stock_pal.md`
- 引擎设计: `doc/design/backtest_engine_upgrade_design.md`

---

## 1. 设计概述

### 1.1 目标

实现一套完整的风控管理系统，在回测引擎中集成以下功能：
1. **仓位控制**：限制单票和总持仓比例
2. **止损止盈**：基于成本价的自动平仓机制
3. **回撤保护**：组合级别的最大回撤保护
4. **波动率管理**：可选的波动率目标控制

### 1.2 设计原则

1. **安全优先**：风控规则优先级高于策略信号
2. **可配置性**：所有风控参数可通过API传入，支持开关
3. **可追溯性**：记录所有风控触发事件和拒绝原因
4. **性能优先**：风控检查不应显著影响回测性能
5. **向后兼容**：不传入风控参数时保持原有行为

### 1.3 非功能性需求

| 需求类型 | 指标 | 说明 |
|---------|------|------|
| 性能 | <1ms | 单次风控检查耗时 |
| 准确性 | 100% | 止损/止盈触发准确性 |
| 可测试性 | >90% | 代码覆盖率 |
| 可维护性 | 高 | 清晰的模块边界和接口 |

---

## 2. 架构设计

### 2.1 模块关系图

```
┌─────────────────────────────────────────────────────────┐
│                  BacktestOrchestrator                   │
│                     (编排层)                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                    TradingEngine                         │
│                   (交易引擎层)                            │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  process_bar(bar_data, signal)                   │  │
│  │                                                   │  │
│  │  1. 更新Portfolio状态                             │  │
│  │  2. RiskManager.check_exit_signals() ───┐        │  │
│  │     └─→ 检查止损/止盈/回撤  ────────────┼──►强制卖出 │
│  │  3. 处理策略卖出信号                      │        │  │
│  │  4. 检查策略买入信号                      │        │  │
│  │  5. RiskManager.check_order_risk() ──────┼──►拒绝/通过 │
│  │  6. 执行通过的订单                        │        │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                    RiskManager                           │
│                    (风控层)                               │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ check_exit_signals()                             │  │
│  │  ├─ _check_stop_loss()        止损检查           │  │
│  │  ├─ _check_stop_profit()      止盈检查           │  │
│  │  └─ _check_drawdown_protection() 回撤保护        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ check_order_risk(order)                          │  │
│  │  ├─ _check_position_limit()   仓位限制检查       │  │
│  │  └─ _check_exposure_limit()   总仓位限制检查     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ _calculate_portfolio_volatility()  可选波动率控制 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 Portfolio & Position                     │
│                  (状态管理层)                             │
│                                                          │
│  - 持仓状态（成本、数量、当前市值）                        │
│  - 账户状态（现金、总权益、历史peak_equity）               │
│  - 历史收益率序列（用于波动率计算）                        │
└─────────────────────────────────────────────────────────┘
```

### 2.2 调用时序

#### 场景1: 买入订单风控检查

```
Strategy Signal (买入)
    │
    ↓
TradingEngine.process_bar()
    │
    ├─→ 创建买入订单 order = {symbol, shares, price}
    │
    ├─→ RiskManager.check_order_risk(order, portfolio)
    │       │
    │       ├─→ 计算新仓位比例 = (order.value + current_position) / equity
    │       ├─→ if 新仓位比例 > max_position_pct:
    │       │       return RiskCheckResult(passed=False, reason="超仓位限制")
    │       │
    │       ├─→ 计算新总仓位 = (total_value + order.value) / equity
    │       └─→ if 新总仓位 > max_total_exposure:
    │               return RiskCheckResult(passed=False, reason="超总仓位限制")
    │
    └─→ if check_result.passed:
            执行订单
        else:
            记录拒绝事件到metadata
```

#### 场景2: 持仓风控检查（每日开盘）

```
TradingEngine.process_bar() - 每日循环
    │
    ├─→ 更新持仓市值（当前价格）
    │
    ├─→ RiskManager.check_exit_signals(portfolio, current_price)
    │       │
    │       ├─→ for each position:
    │       │     │
    │       │     ├─→ 止损检查:
    │       │     │   if current_price < cost_price * (1 - stop_loss_pct):
    │       │     │       add forced_sell_order (reason: "止损")
    │       │     │
    │       │     └─→ 止盈检查:
    │       │         if current_price > cost_price * (1 + stop_profit_pct):
    │       │             add forced_sell_order (reason: "止盈")
    │       │
    │       └─→ 回撤保护检查:
    │           if current_equity < peak_equity * (1 - max_drawdown_pct):
    │               add forced_sell_all_orders (reason: "回撤保护")
    │
    └─→ 执行强制卖出订单（优先级高于策略信号）
```

### 2.3 模块职责

#### RiskManager

**职责**：
- 封装所有风控规则逻辑
- 提供买入前检查和持仓监控接口
- 生成风控触发事件记录

**依赖**：
- Portfolio（读取持仓和账户状态）
- RiskConfig（风控参数配置）

**被依赖**：
- TradingEngine（交易引擎调用）

**关键方法**：
```python
class RiskManager:
    def check_order_risk(order, portfolio) -> RiskCheckResult
    def check_exit_signals(portfolio, current_data) -> List[ForcedOrder]
    def update_peak_equity(current_equity) -> None
```

#### TradingEngine

**新增职责**：
- 在买入前调用风控检查
- 在每日开盘后优先处理风控退出信号
- 记录风控事件到metadata

**变更点**：
- `process_bar()` 方法增加风控调用逻辑
- `metadata` 增加 `risk_events` 字段

---

## 3. 数据结构设计

### 3.1 配置类

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class RiskConfig:
    """风控配置参数"""

    # ============ 仓位控制 ============
    max_position_pct: float = 1.0
    """单票最大仓位比例（相对于总权益）
    - 默认1.0（100%，即不限制）
    - 示例：0.3表示单票最多占30%
    """

    max_total_exposure: float = 1.0
    """最大总仓位比例（所有持仓市值/总权益）
    - 默认1.0（100%，即满仓）
    - 示例：0.95表示最多保留5%现金
    """

    # ============ 止损止盈 ============
    stop_loss_pct: Optional[float] = None
    """止损线（亏损比例）
    - None表示不启用
    - 示例：0.1表示亏损10%时止损
    - 触发条件：current_price < cost_price * (1 - stop_loss_pct)
    """

    stop_profit_pct: Optional[float] = None
    """止盈线（盈利比例）
    - None表示不启用
    - 示例：0.2表示盈利20%时止盈
    - 触发条件：current_price > cost_price * (1 + stop_profit_pct)
    """

    enable_trailing_stop: bool = False
    """是否启用移动止损（暂不实现，预留字段）"""

    # ============ 组合风控 ============
    max_drawdown_pct: Optional[float] = None
    """最大回撤保护阈值
    - None表示不启用
    - 示例：0.2表示从最高点回撤20%时清仓
    - 触发条件：current_equity < peak_equity * (1 - max_drawdown_pct)
    """

    volatility_target: Optional[float] = None
    """目标波动率（年化）- V2功能，暂不实现
    - None表示不启用
    - 示例：0.15表示目标年化波动率15%
    """

    volatility_lookback: int = 20
    """波动率计算回溯期（交易日数）- V2功能"""

    # ============ 其他 ============
    max_leverage: float = 1.0
    """最大杠杆倍数（现货交易固定为1）"""

    def __post_init__(self):
        """参数验证"""
        if not 0 < self.max_position_pct <= 1.0:
            raise ValueError("max_position_pct must be in (0, 1]")
        if not 0 < self.max_total_exposure <= 1.0:
            raise ValueError("max_total_exposure must be in (0, 1]")
        if self.stop_loss_pct is not None and not 0 < self.stop_loss_pct < 1:
            raise ValueError("stop_loss_pct must be in (0, 1)")
        if self.stop_profit_pct is not None and self.stop_profit_pct <= 0:
            raise ValueError("stop_profit_pct must be > 0")
        if self.max_drawdown_pct is not None and not 0 < self.max_drawdown_pct < 1:
            raise ValueError("max_drawdown_pct must be in (0, 1)")
```

### 3.2 检查结果类

```python
from enum import Enum
from typing import Optional

class RiskCheckStatus(str, Enum):
    """风控检查状态"""
    PASSED = "passed"           # 通过
    REJECTED = "rejected"       # 拒绝
    ADJUSTED = "adjusted"       # 调整（暂不实现，预留）

@dataclass
class RiskCheckResult:
    """订单风控检查结果"""

    status: RiskCheckStatus
    """检查状态"""

    reason: Optional[str] = None
    """拒绝原因（status=REJECTED时必填）"""

    original_shares: Optional[int] = None
    """原始订单股数（用于记录）"""

    adjusted_shares: Optional[int] = None
    """调整后股数（status=ADJUSTED时使用，V2功能）"""

    @property
    def passed(self) -> bool:
        """是否通过"""
        return self.status == RiskCheckStatus.PASSED
```

### 3.3 强制订单类

```python
@dataclass
class ForcedOrder:
    """风控触发的强制订单"""

    symbol: str
    """股票代码"""

    shares: int
    """卖出股数"""

    reason: str
    """触发原因：'stop_loss'/'stop_profit'/'drawdown_protection'"""

    trigger_price: float
    """触发时的价格"""

    cost_price: Optional[float] = None
    """成本价（止损止盈时记录）"""

    pnl_pct: Optional[float] = None
    """盈亏比例（止损止盈时计算）"""
```

### 3.4 风控事件记录

```python
@dataclass
class RiskEvent:
    """风控事件记录（用于metadata）"""

    date: str
    """触发日期（YYYY-MM-DD）"""

    event_type: str
    """事件类型：'order_rejected'/'forced_exit'"""

    symbol: str
    """股票代码"""

    reason: str
    """触发原因"""

    details: dict
    """详细信息（价格、比例等）"""

    timestamp: str
    """记录时间戳（ISO格式）"""
```

---

## 4. 核心算法设计

### 4.1 仓位限制检查

**算法：check_position_limit**

```python
def _check_position_limit(
    self,
    order: Order,
    portfolio: Portfolio
) -> RiskCheckResult:
    """检查单票仓位限制"""

    # 1. 计算当前持仓市值
    current_position_value = 0
    if order.symbol in portfolio.positions:
        position = portfolio.positions[order.symbol]
        current_position_value = position.shares * order.price

    # 2. 计算订单金额
    order_value = order.shares * order.price

    # 3. 计算新仓位占比
    total_equity = portfolio.total_equity
    new_position_value = current_position_value + order_value
    new_position_pct = new_position_value / total_equity

    # 4. 判断是否超限
    if new_position_pct > self.config.max_position_pct:
        return RiskCheckResult(
            status=RiskCheckStatus.REJECTED,
            reason=f"单票仓位{new_position_pct:.2%}超过限制{self.config.max_position_pct:.2%}",
            original_shares=order.shares
        )

    return RiskCheckResult(status=RiskCheckStatus.PASSED)
```

**复杂度**: O(1)
**边界情况**:
- 首次买入（无现有持仓）
- 加仓（已有持仓）
- 满仓情况（total_equity全部在持仓中）

### 4.2 止损检查

**算法：check_stop_loss**

```python
def _check_stop_loss(
    self,
    position: Position,
    current_price: float
) -> Optional[ForcedOrder]:
    """检查单个持仓是否触发止损"""

    # 1. 未配置止损线则跳过
    if self.config.stop_loss_pct is None:
        return None

    # 2. 计算止损价格
    stop_loss_price = position.cost_price * (1 - self.config.stop_loss_pct)

    # 3. 判断是否触发
    if current_price <= stop_loss_price:
        pnl_pct = (current_price - position.cost_price) / position.cost_price

        return ForcedOrder(
            symbol=position.symbol,
            shares=position.shares,
            reason="stop_loss",
            trigger_price=current_price,
            cost_price=position.cost_price,
            pnl_pct=pnl_pct
        )

    return None
```

**关键点**:
1. 使用 `<=` 而非 `<`（确保边界触发）
2. 记录实际亏损比例（用于后续分析）
3. 全仓卖出（不支持部分止损）

### 4.3 回撤保护检查

**算法：check_drawdown_protection**

```python
def _check_drawdown_protection(
    self,
    portfolio: Portfolio
) -> List[ForcedOrder]:
    """检查组合回撤保护"""

    # 1. 未配置回撤保护则跳过
    if self.config.max_drawdown_pct is None:
        return []

    # 2. 更新历史最高权益
    current_equity = portfolio.total_equity
    self.peak_equity = max(self.peak_equity, current_equity)

    # 3. 计算当前回撤
    drawdown = (self.peak_equity - current_equity) / self.peak_equity

    # 4. 判断是否触发
    if drawdown >= self.config.max_drawdown_pct:
        # 清空所有持仓
        forced_orders = []
        for symbol, position in portfolio.positions.items():
            forced_orders.append(
                ForcedOrder(
                    symbol=symbol,
                    shares=position.shares,
                    reason="drawdown_protection",
                    trigger_price=portfolio.current_prices[symbol],
                    pnl_pct=drawdown  # 记录实际回撤
                )
            )
        return forced_orders

    return []
```

**关键点**:
1. `peak_equity` 需要在RiskManager中持久化（整个回测周期内）
2. 初始化时 `peak_equity = initial_capital`
3. 回撤保护触发后立即清仓（不等待策略信号）
4. 清仓后策略仍可继续产生买入信号（允许重新入场）

### 4.4 波动率目标控制（V2，暂不实现）

**算法概述**:
```python
def _check_volatility_target(
    self,
    portfolio: Portfolio
) -> float:
    """计算建议仓位缩放因子（基于波动率目标）"""

    # 1. 计算最近N日收益率
    returns = portfolio.equity_history[-self.config.volatility_lookback:]

    # 2. 计算年化波动率
    daily_vol = np.std(returns)
    annual_vol = daily_vol * np.sqrt(252)

    # 3. 计算缩放因子
    if annual_vol > self.config.volatility_target:
        scale_factor = self.config.volatility_target / annual_vol
    else:
        scale_factor = 1.0

    return scale_factor  # 用于调整新订单规模
```

**暂不实现原因**:
- 需要Portfolio记录每日权益变化历史
- 实现复杂度较高，V1先实现基础风控

---

## 5. API集成设计

### 5.1 请求参数扩展

**现有请求体**:
```json
{
  "symbol": "600000",
  "strategy_id": "ma_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "initial_capital": 100000,
  "commission_rate": 0.0003,
  "params": {...}
}
```

**新增风控参数**（可选）:
```json
{
  "symbol": "600000",
  "strategy_id": "ma_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "initial_capital": 100000,
  "commission_rate": 0.0003,
  "params": {...},

  "risk_config": {
    "max_position_pct": 0.3,
    "max_total_exposure": 0.95,
    "stop_loss_pct": 0.1,
    "stop_profit_pct": 0.2,
    "max_drawdown_pct": 0.15
  }
}
```

### 5.2 响应数据扩展

**新增字段**:
```json
{
  "results": {
    // 原有指标...
    "total_return": 0.25,
    "sharpe_ratio": 1.2,

    // 新增风控影响指标
    "risk_stats": {
      "stop_loss_count": 3,           // 止损次数
      "stop_profit_count": 5,          // 止盈次数
      "drawdown_protection_count": 1,  // 回撤保护触发次数
      "rejected_orders_count": 2       // 拒绝订单次数
    }
  },

  "trades": [
    {
      "date": "2023-05-15",
      "action": "sell",
      "shares": 1000,
      "price": 12.5,
      "amount": 12500,
      "commission": 3.75,
      "reason": "stop_loss",           // 新增字段：退出原因
      "pnl": -1250,
      "pnl_pct": -0.10
    }
  ],

  "metadata": {
    // 新增风控事件记录
    "risk_events": [
      {
        "date": "2023-05-15",
        "event_type": "forced_exit",
        "symbol": "600000",
        "reason": "stop_loss",
        "details": {
          "trigger_price": 12.5,
          "cost_price": 13.89,
          "loss_pct": -0.10
        }
      },
      {
        "date": "2023-06-20",
        "event_type": "order_rejected",
        "symbol": "600000",
        "reason": "仓位限制",
        "details": {
          "intended_shares": 2000,
          "current_position_pct": 0.25,
          "max_allowed_pct": 0.30
        }
      }
    ]
  }
}
```

### 5.3 API层变更

**文件**: `backend/app/api/v1/backtest.py`

```python
from app.backtest.risk_manager import RiskConfig

@backtest_ns.route('/')
class BacktestResource(Resource):
    def post(self):
        """运行回测"""
        data = request.get_json()

        # ... 原有参数验证 ...

        # 解析风控配置（可选）
        risk_config = None
        if 'risk_config' in data:
            risk_config = RiskConfig(**data['risk_config'])

        # 传递给orchestrator
        result = orchestrator.run(
            symbol=symbol,
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            strategy_params=params,
            risk_config=risk_config  # 新增参数
        )

        return result, 200
```

---

## 6. 测试设计

### 6.1 单元测试计划

**文件结构**:
```
backend/tests/
├── test_risk_manager.py          # RiskManager核心逻辑
├── test_risk_config.py            # RiskConfig参数验证
└── test_integration_risk.py       # 集成测试（TradingEngine + RiskManager）
```

**测试用例清单**:

#### 6.1.1 RiskConfig参数验证

```python
def test_risk_config_valid_params():
    """正常参数验证"""
    config = RiskConfig(
        max_position_pct=0.3,
        stop_loss_pct=0.1,
        max_drawdown_pct=0.2
    )
    assert config.max_position_pct == 0.3

def test_risk_config_invalid_position_pct():
    """仓位比例超出范围"""
    with pytest.raises(ValueError):
        RiskConfig(max_position_pct=1.5)

def test_risk_config_invalid_stop_loss():
    """止损比例为负"""
    with pytest.raises(ValueError):
        RiskConfig(stop_loss_pct=-0.1)
```

#### 6.1.2 仓位限制检查

```python
def test_position_limit_first_buy(risk_manager, portfolio):
    """首次买入，不超限"""
    order = Order(symbol='600000', shares=1000, price=10.0)
    result = risk_manager._check_position_limit(order, portfolio)
    assert result.passed is True

def test_position_limit_exceeded(risk_manager, portfolio):
    """仓位超限，拒绝订单"""
    # 设置30%仓位限制
    risk_manager.config.max_position_pct = 0.3

    # 已持有20%仓位，尝试再买15%
    portfolio.positions['600000'] = Position(...)
    order = Order(symbol='600000', shares=1500, price=10.0)

    result = risk_manager._check_position_limit(order, portfolio)
    assert result.passed is False
    assert "超过限制" in result.reason

def test_position_limit_boundary(risk_manager, portfolio):
    """边界测试：正好30%仓位"""
    risk_manager.config.max_position_pct = 0.3
    portfolio.total_equity = 100000

    order = Order(symbol='600000', shares=3000, price=10.0)  # 30000元
    result = risk_manager._check_position_limit(order, portfolio)
    assert result.passed is True  # 边界值应通过
```

#### 6.1.3 止损检查

```python
def test_stop_loss_triggered(risk_manager):
    """止损触发"""
    risk_manager.config.stop_loss_pct = 0.1  # 10%止损

    position = Position(
        symbol='600000',
        shares=1000,
        cost_price=10.0
    )

    current_price = 8.9  # 下跌11%
    forced_order = risk_manager._check_stop_loss(position, current_price)

    assert forced_order is not None
    assert forced_order.reason == "stop_loss"
    assert forced_order.shares == 1000
    assert forced_order.pnl_pct == pytest.approx(-0.11, abs=0.01)

def test_stop_loss_not_triggered(risk_manager):
    """未触发止损"""
    risk_manager.config.stop_loss_pct = 0.1
    position = Position(symbol='600000', shares=1000, cost_price=10.0)

    current_price = 9.5  # 下跌5%
    forced_order = risk_manager._check_stop_loss(position, current_price)

    assert forced_order is None

def test_stop_loss_disabled(risk_manager):
    """止损未启用"""
    risk_manager.config.stop_loss_pct = None
    position = Position(symbol='600000', shares=1000, cost_price=10.0)

    current_price = 5.0  # 下跌50%
    forced_order = risk_manager._check_stop_loss(position, current_price)

    assert forced_order is None  # 未启用，不触发

def test_stop_loss_boundary(risk_manager):
    """边界测试：正好-10%"""
    risk_manager.config.stop_loss_pct = 0.1
    position = Position(symbol='600000', shares=1000, cost_price=10.0)

    current_price = 9.0  # 正好-10%
    forced_order = risk_manager._check_stop_loss(position, current_price)

    assert forced_order is not None  # 边界值应触发（使用<=）
```

#### 6.1.4 回撤保护检查

```python
def test_drawdown_protection_triggered(risk_manager, portfolio):
    """回撤保护触发"""
    risk_manager.config.max_drawdown_pct = 0.2  # 20%回撤保护
    risk_manager.peak_equity = 120000  # 历史最高权益

    portfolio.total_equity = 95000  # 当前权益（回撤20.8%）
    portfolio.positions = {
        '600000': Position(symbol='600000', shares=1000, cost_price=10.0),
        '000001': Position(symbol='000001', shares=500, cost_price=20.0)
    }

    forced_orders = risk_manager._check_drawdown_protection(portfolio)

    assert len(forced_orders) == 2  # 清空所有持仓
    assert all(order.reason == "drawdown_protection" for order in forced_orders)

def test_drawdown_protection_update_peak(risk_manager, portfolio):
    """更新历史最高权益"""
    risk_manager.config.max_drawdown_pct = 0.2
    risk_manager.peak_equity = 100000

    portfolio.total_equity = 110000  # 创新高
    forced_orders = risk_manager._check_drawdown_protection(portfolio)

    assert risk_manager.peak_equity == 110000  # peak_equity已更新
    assert len(forced_orders) == 0
```

#### 6.1.5 集成测试

```python
def test_integration_stop_loss_executed(trading_engine):
    """集成测试：止损单正确执行"""
    # 设置止损10%
    trading_engine.risk_manager.config.stop_loss_pct = 0.1

    # 第1天：买入，成本10元
    bar1 = BarData(date='2023-01-03', open=10, high=10.5, low=9.8, close=10, volume=1000000)
    signal1 = Signal(buy_signal=True, sell_signal=False)
    trading_engine.process_bar(bar1, signal1)

    assert '600000' in trading_engine.portfolio.positions
    assert trading_engine.portfolio.positions['600000'].cost_price == 10.0

    # 第2天：价格跌至8.5，触发止损
    bar2 = BarData(date='2023-01-04', open=8.5, high=8.7, low=8.3, close=8.5, volume=1200000)
    signal2 = Signal(buy_signal=False, sell_signal=False)  # 策略无信号
    trading_engine.process_bar(bar2, signal2)

    # 验证已清仓
    assert '600000' not in trading_engine.portfolio.positions

    # 验证有强制卖出交易记录
    last_trade = trading_engine.trades[-1]
    assert last_trade['action'] == 'sell'
    assert last_trade['reason'] == 'stop_loss'
    assert last_trade['pnl_pct'] == pytest.approx(-0.15, abs=0.01)

def test_integration_position_limit_rejection(trading_engine):
    """集成测试：仓位限制拒绝订单"""
    # 设置30%仓位限制
    trading_engine.risk_manager.config.max_position_pct = 0.3
    trading_engine.portfolio.total_equity = 100000

    # 尝试买入40000元（40%仓位）
    bar = BarData(date='2023-01-03', open=10, high=10.5, low=9.8, close=10, volume=1000000)
    signal = Signal(buy_signal=True, sell_signal=False)

    trading_engine.process_bar(bar, signal)

    # 验证订单被拒绝
    assert '600000' not in trading_engine.portfolio.positions
    assert trading_engine.portfolio.cash == 100000  # 现金未变

    # 验证有风控事件记录
    assert len(trading_engine.metadata['risk_events']) > 0
    event = trading_engine.metadata['risk_events'][-1]
    assert event['event_type'] == 'order_rejected'
    assert '超过限制' in event['reason']
```

### 6.2 测试覆盖率目标

| 模块 | 目标覆盖率 | 关键路径 |
|------|-----------|---------|
| RiskManager | 95% | 所有风控规则逻辑 |
| RiskConfig | 100% | 参数验证 |
| TradingEngine集成 | 90% | 风控调用流程 |

### 6.3 性能测试

```python
def test_risk_check_performance():
    """风控检查性能测试"""
    risk_manager = RiskManager(config=RiskConfig())
    portfolio = create_mock_portfolio()
    order = Order(symbol='600000', shares=1000, price=10.0)

    import time
    start = time.perf_counter()

    for _ in range(10000):
        risk_manager.check_order_risk(order, portfolio)

    elapsed = time.perf_counter() - start
    avg_time = elapsed / 10000

    assert avg_time < 0.001  # 平均每次检查<1ms
```

---

## 7. 开发计划

### 7.1 任务分解

| 任务ID | 任务名称 | 估时 | 依赖 | 负责人 |
|-------|---------|------|------|--------|
| **RISK-001** | 数据结构实现 | 2h | - | TBD |
| RISK-001-1 | RiskConfig类实现 | 1h | - | |
| RISK-001-2 | RiskCheckResult类实现 | 0.5h | - | |
| RISK-001-3 | ForcedOrder/RiskEvent类实现 | 0.5h | - | |
| **RISK-002** | RiskManager核心逻辑 | 6h | RISK-001 | TBD |
| RISK-002-1 | 仓位限制检查实现 | 1.5h | RISK-001 | |
| RISK-002-2 | 止损检查实现 | 1.5h | RISK-001 | |
| RISK-002-3 | 止盈检查实现 | 1h | RISK-001 | |
| RISK-002-4 | 回撤保护检查实现 | 2h | RISK-001 | |
| **RISK-003** | TradingEngine集成 | 4h | RISK-002 | TBD |
| RISK-003-1 | process_bar增加风控调用 | 2h | RISK-002 | |
| RISK-003-2 | metadata增加risk_events | 1h | RISK-002 | |
| RISK-003-3 | Trade记录增加reason字段 | 1h | RISK-002 | |
| **RISK-004** | API层集成 | 3h | RISK-003 | TBD |
| RISK-004-1 | 请求参数解析risk_config | 1h | RISK-003 | |
| RISK-004-2 | 响应增加risk_stats | 1h | RISK-003 | |
| RISK-004-3 | BacktestOrchestrator传递风控配置 | 1h | RISK-003 | |
| **RISK-005** | 单元测试 | 8h | RISK-002 | TBD |
| RISK-005-1 | RiskConfig测试 | 1h | RISK-001 | |
| RISK-005-2 | 仓位限制测试（含边界） | 2h | RISK-002 | |
| RISK-005-3 | 止损止盈测试（含边界） | 2h | RISK-002 | |
| RISK-005-4 | 回撤保护测试 | 1.5h | RISK-002 | |
| RISK-005-5 | 集成测试 | 1.5h | RISK-003 | |
| **RISK-006** | 文档与示例 | 2h | RISK-004 | TBD |
| RISK-006-1 | API文档更新 | 1h | RISK-004 | |
| RISK-006-2 | 使用示例（Postman） | 1h | RISK-004 | |

**总计**: 25小时（约3个工作日）

### 7.2 开发时间线

```
Day 1 (8h):
  ├─ Morning (4h):
  │   ├─ RISK-001: 数据结构实现 (2h)
  │   └─ RISK-002-1: 仓位限制检查 (1.5h)
  │   └─ RISK-002-2: 止损检查 (0.5h)
  │
  └─ Afternoon (4h):
      ├─ RISK-002-2: 止损检查完成 (1h)
      ├─ RISK-002-3: 止盈检查 (1h)
      └─ RISK-002-4: 回撤保护 (2h)

Day 2 (8h):
  ├─ Morning (4h):
  │   ├─ RISK-003: TradingEngine集成 (4h)
  │
  └─ Afternoon (4h):
      ├─ RISK-004: API层集成 (3h)
      └─ RISK-005-1: RiskConfig测试 (1h)

Day 3 (8h):
  ├─ Morning (4h):
  │   ├─ RISK-005-2: 仓位限制测试 (2h)
  │   └─ RISK-005-3: 止损止盈测试 (2h)
  │
  └─ Afternoon (4h):
      ├─ RISK-005-4: 回撤保护测试 (1.5h)
      ├─ RISK-005-5: 集成测试 (1.5h)
      └─ RISK-006: 文档与示例 (2h) [可并行]

Buffer: 1h (处理意外问题)
```

### 7.3 依赖关系图

```
RISK-001 (数据结构)
    │
    ├───→ RISK-002 (RiskManager核心)
    │         │
    │         └───→ RISK-003 (TradingEngine集成)
    │                   │
    │                   └───→ RISK-004 (API集成)
    │
    └───→ RISK-005 (测试)
              │
              └───→ RISK-006 (文档)
```

### 7.4 关键里程碑

| 里程碑 | 交付物 | 验收标准 | 截止时间 |
|--------|--------|---------|---------|
| M1: 核心逻辑完成 | RiskManager类 | 所有风控规则通过单元测试 | Day 1 EOD |
| M2: 引擎集成完成 | TradingEngine集成 | 集成测试通过，无回归问题 | Day 2 EOD |
| M3: API可用 | 完整API + 文档 | Postman测试通过 | Day 3 Noon |
| M4: 质量保证 | 测试报告 | 覆盖率>90%，性能达标 | Day 3 EOD |

---

## 8. 验收标准

### 8.1 功能验收

#### 8.1.1 仓位限制

- [ ] 单票仓位限制生效，超限订单被拒绝
- [ ] 总仓位限制生效
- [ ] 拒绝原因正确记录到metadata
- [ ] 边界情况（正好30%仓位）处理正确

#### 8.1.2 止损止盈

- [ ] 止损线触发时强制卖出
- [ ] 止盈线触发时强制卖出
- [ ] 未启用时不触发（stop_loss_pct=None）
- [ ] 触发价格和盈亏比例正确记录
- [ ] 止损优先级高于策略买入信号

#### 8.1.3 回撤保护

- [ ] 回撤达到阈值时清空所有持仓
- [ ] peak_equity正确跟踪历史最高权益
- [ ] 清仓后策略可继续运行
- [ ] 多持仓场景下全部清空

#### 8.1.4 API集成

- [ ] risk_config参数可正确解析
- [ ] 无效参数返回400错误
- [ ] 响应包含risk_stats字段
- [ ] Trade记录包含reason字段（止损/止盈时）
- [ ] metadata包含完整的risk_events

### 8.2 代码质量验收

- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有测试通过（pytest）
- [ ] 代码符合Black格式（make format-backend）
- [ ] 无flake8告警（make lint-backend）
- [ ] 所有类和方法有完整docstring
- [ ] 类型注解完整（使用typing）

### 8.3 性能验收

- [ ] 单次风控检查耗时 < 1ms
- [ ] 完整回测性能无明显下降（<5%）
- [ ] 内存占用无异常增长

### 8.4 文档验收

- [ ] API文档已更新（包含风控参数说明）
- [ ] 提供Postman示例请求
- [ ] 代码注释清晰（关键算法有解释）
- [ ] 本设计文档与实现一致

---

## 9. 风险与注意事项

### 9.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 风控规则与策略信号冲突 | 高 | 中 | 明确优先级：风控 > 策略信号 |
| peak_equity状态管理错误 | 高 | 低 | 单元测试覆盖状态更新逻辑 |
| 止损触发时机不准确 | 中 | 中 | 使用开盘价触发，边界值使用<= |
| 性能下降 | 低 | 低 | 性能测试，优化热点代码 |

### 9.2 产品风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 止损阈值设置不当 | 中 | 高 | 提供推荐值，支持关闭 |
| 回撤保护过度敏感 | 中 | 中 | 可配置，提供对比分析 |
| 用户不理解风控参数 | 低 | 高 | 详细文档 + 前端提示 |

### 9.3 注意事项

1. **向后兼容性**：
   - risk_config为可选参数，不传时保持原有行为
   - 不影响现有API的功能

2. **止损止盈触发时机**：
   - 使用每日开盘价触发（不使用盘中价格）
   - 确保回测可重现性

3. **风控优先级**：
   - 风控退出信号 > 策略卖出信号 > 策略买入信号
   - 同一天既有止损又有策略买入信号时，先执行止损

4. **清仓后的行为**：
   - 回撤保护触发清仓后，策略仍可继续运行
   - 不锁定账户，允许重新入场

5. **测试数据准备**：
   - 需要构造触发各类风控规则的市场数据
   - 使用mock数据而非真实股票数据

---

## 10. 后续优化方向

### 10.1 V2功能（P1）

1. **移动止损（Trailing Stop）**：
   - 止损线随价格上涨而上移
   - 锁定浮盈，扩大盈利空间

2. **波动率目标控制**：
   - 动态调整仓位规模
   - 实现风险平价策略

3. **部分止损**：
   - 支持止损50%仓位（而非全部）
   - 更灵活的风控策略

4. **分级止损**：
   - 多个止损阈值（-5%减半仓，-10%清仓）

### 10.2 前端集成（P1）

1. **风控配置面板**：
   - 表单输入风控参数
   - 预设模板（保守/平衡/激进）

2. **风控事件可视化**：
   - K线图上标注止损/止盈点
   - 权益曲线上标注回撤保护触发

3. **对比分析**：
   - 显示有/无风控的回测结果对比
   - 量化风控的影响

### 10.3 高级风控（Future）

1. **组合级止损**：
   - 基于组合整体盈亏的止损
   - 与单票止损配合使用

2. **条件风控**：
   - 市场环境判断（如VIX指数）
   - 动态调整风控参数

3. **风控回测报告**：
   - 风控触发统计
   - 风控效果评估

---

## 11. 参考资料

### 11.1 内部文档

- PRD: `doc/requirements/product_requirements_stock_pal.md`
- 回测引擎设计: `doc/design/backtest_engine_upgrade_design.md`
- 上级设计: `doc/design/backtest_post_mvp_enhancements.md`

### 11.2 外部参考

- [《Quantitative Trading》](https://www.quantstart.com/) - 风控章节
- [Backtrader风控文档](https://www.backtrader.com/docu/analyzers/) - 风控分析器
- [Zipline风控实现](https://github.com/quantopian/zipline) - 开源回测框架

### 11.3 相关论坛讨论

- [量化交易中的风控管理](https://www.zhihu.com/question/xxxxx)
- [止损策略的有效性](https://www.investopedia.com/articles/stocks/09/use-stop-loss.asp)

---

## 附录A：代码骨架

### A.1 RiskManager骨架

```python
"""
风控管理器模块

负责在回测过程中执行风控规则检查，包括：
- 订单风控：仓位限制
- 持仓风控：止损、止盈、回撤保护
"""

from typing import List, Optional
from dataclasses import dataclass
from app.backtest.portfolio import Portfolio, Position
from app.backtest.order import Order


class RiskManager:
    """风控管理器"""

    def __init__(self, config: RiskConfig, initial_capital: float):
        """
        初始化风控管理器

        Args:
            config: 风控配置
            initial_capital: 初始资金（用于初始化peak_equity）
        """
        self.config = config
        self.peak_equity = initial_capital

    def check_order_risk(
        self,
        order: Order,
        portfolio: Portfolio
    ) -> RiskCheckResult:
        """
        检查订单是否通过风控

        在TradingEngine执行买入订单前调用

        Args:
            order: 待执行订单
            portfolio: 当前组合状态

        Returns:
            RiskCheckResult: 检查结果（通过/拒绝）
        """
        # 1. 检查单票仓位限制
        result = self._check_position_limit(order, portfolio)
        if not result.passed:
            return result

        # 2. 检查总仓位限制
        result = self._check_exposure_limit(order, portfolio)
        if not result.passed:
            return result

        return RiskCheckResult(status=RiskCheckStatus.PASSED)

    def check_exit_signals(
        self,
        portfolio: Portfolio,
        current_data: dict  # {symbol: current_price}
    ) -> List[ForcedOrder]:
        """
        检查是否触发风控退出信号

        在TradingEngine.process_bar开始时调用

        Args:
            portfolio: 当前组合状态
            current_data: 当前价格数据

        Returns:
            List[ForcedOrder]: 强制卖出订单列表
        """
        forced_orders = []

        # 1. 检查回撤保护（优先级最高）
        drawdown_orders = self._check_drawdown_protection(portfolio)
        if drawdown_orders:
            return drawdown_orders  # 触发回撤保护时立即返回（清仓）

        # 2. 检查每个持仓的止损止盈
        for symbol, position in portfolio.positions.items():
            current_price = current_data.get(symbol)
            if current_price is None:
                continue

            # 止损检查
            stop_loss_order = self._check_stop_loss(position, current_price)
            if stop_loss_order:
                forced_orders.append(stop_loss_order)
                continue  # 止损优先，不再检查止盈

            # 止盈检查
            stop_profit_order = self._check_stop_profit(position, current_price)
            if stop_profit_order:
                forced_orders.append(stop_profit_order)

        return forced_orders

    # ========== 私有方法 ==========

    def _check_position_limit(self, order: Order, portfolio: Portfolio) -> RiskCheckResult:
        """检查单票仓位限制"""
        pass  # 见第4节算法设计

    def _check_exposure_limit(self, order: Order, portfolio: Portfolio) -> RiskCheckResult:
        """检查总仓位限制"""
        pass

    def _check_stop_loss(self, position: Position, current_price: float) -> Optional[ForcedOrder]:
        """检查止损"""
        pass  # 见第4节算法设计

    def _check_stop_profit(self, position: Position, current_price: float) -> Optional[ForcedOrder]:
        """检查止盈"""
        pass

    def _check_drawdown_protection(self, portfolio: Portfolio) -> List[ForcedOrder]:
        """检查回撤保护"""
        pass  # 见第4节算法设计
```

### A.2 TradingEngine集成骨架

```python
class TradingEngine:
    """交易引擎（增加风控集成）"""

    def __init__(self, ..., risk_config: Optional[RiskConfig] = None):
        # 原有初始化...

        # 新增风控管理器
        if risk_config:
            self.risk_manager = RiskManager(risk_config, initial_capital)
        else:
            self.risk_manager = None

    def process_bar(self, bar_data, signal):
        """处理单根K线（增加风控逻辑）"""

        # 1. 更新持仓市值
        self._update_positions(bar_data)

        # 2. 检查风控退出信号（优先级最高）
        if self.risk_manager:
            current_data = {self.symbol: bar_data.close}
            forced_orders = self.risk_manager.check_exit_signals(
                self.portfolio,
                current_data
            )

            # 执行强制卖出
            for forced_order in forced_orders:
                self._execute_forced_order(forced_order, bar_data.date)

        # 3. 处理策略卖出信号
        if signal.sell_signal:
            self._execute_sell(bar_data)

        # 4. 处理策略买入信号（需要通过风控检查）
        if signal.buy_signal:
            order = self._create_buy_order(bar_data)

            # 风控检查
            if self.risk_manager:
                risk_result = self.risk_manager.check_order_risk(order, self.portfolio)

                if risk_result.passed:
                    self._execute_order(order, bar_data.date)
                else:
                    # 记录拒绝事件
                    self._record_risk_event(
                        date=bar_data.date,
                        event_type="order_rejected",
                        symbol=self.symbol,
                        reason=risk_result.reason,
                        details={
                            "intended_shares": order.shares,
                            "price": order.price
                        }
                    )
            else:
                # 无风控时直接执行
                self._execute_order(order, bar_data.date)

    def _execute_forced_order(self, forced_order: ForcedOrder, date: str):
        """执行风控强制订单"""
        # 类似_execute_sell，但reason字段使用forced_order.reason
        pass

    def _record_risk_event(self, date, event_type, symbol, reason, details):
        """记录风控事件到metadata"""
        event = RiskEvent(
            date=date,
            event_type=event_type,
            symbol=symbol,
            reason=reason,
            details=details,
            timestamp=datetime.now().isoformat()
        )
        self.metadata['risk_events'].append(event.__dict__)
```

---

## 附录B：示例请求

### B.1 启用仓位限制和止损

```bash
POST http://localhost:4001/api/v1/backtest
Content-Type: application/json

{
  "symbol": "600000",
  "strategy_id": "ma_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "initial_capital": 100000,
  "commission_rate": 0.0003,
  "params": {
    "short_window": 5,
    "long_window": 20
  },
  "risk_config": {
    "max_position_pct": 0.5,
    "stop_loss_pct": 0.08
  }
}
```

### B.2 启用完整风控

```bash
POST http://localhost:4001/api/v1/backtest
Content-Type: application/json

{
  "symbol": "600000",
  "strategy_id": "macd_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "initial_capital": 100000,
  "commission_rate": 0.0003,
  "risk_config": {
    "max_position_pct": 0.3,
    "max_total_exposure": 0.95,
    "stop_loss_pct": 0.10,
    "stop_profit_pct": 0.20,
    "max_drawdown_pct": 0.15
  }
}
```

### B.3 无风控（兼容旧版）

```bash
POST http://localhost:4001/api/v1/backtest
Content-Type: application/json

{
  "symbol": "600000",
  "strategy_id": "ma_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "initial_capital": 100000,
  "commission_rate": 0.0003
}
```

---

**文档状态**: ✅ 详细设计完成
**下一步**: 按开发计划开始实施（Day 1: 数据结构 + RiskManager核心）
