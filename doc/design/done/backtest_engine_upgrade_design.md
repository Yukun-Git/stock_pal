# 回测引擎升级详细设计文档

**版本**: v1.1
**创建时间**: 2025-11-12
**最后更新**: 2025-11-12
**负责人**: TBD
**状态**: 设计中

---

## 重要关联文档

📘 **[多市场交易规则架构设计](./multi_market_trading_rules_design.md)** - 本文档的规则验证部分基于多市场三层架构（市场-板块-渠道）

---

## 目录

1. [需求分析](#1-需求分析)
2. [现状分析与差距](#2-现状分析与差距)
3. [总体架构设计](#3-总体架构设计)
4. [核心模块设计](#4-核心模块设计)
5. [数据模型设计](#5-数据模型设计)
6. [接口设计](#6-接口设计)
7. [技术实现细节](#7-技术实现细节)
8. [性能优化方案](#8-性能优化方案)
9. [测试策略](#9-测试策略)
10. [风险与挑战](#10-风险与挑战)
11. [开发计划](#11-开发计划)
12. [附录](#12-附录)

---

## 1. 需求分析

### 1.1 业务需求

根据 PRD（`doc/requirements/product_requirements_stock_pal.md`），回测引擎需要满足以下核心要求：

**必须（MUST）**：
- 满足**多市场**交易规则（当前：A股、港股；未来：美股等）
  - A股：T+1、板块差异化涨跌停（主板±10%、创业板±20%、科创板±20%、北交所±30%、ST±5%）、停牌约束
  - 港股：T+2、无涨跌停、手数制、不同费率结构
  - 港股通：混合规则（T+0交易但T+2资金交割、港股规则+A股渠道费用）
  - 规则**三层架构**（市场-板块-渠道），可插拔、可配置，不硬编码
- 精确的成本/滑点模型
- 可复现性（相同输入 → 相同输出）
- 扩展性能指标（年化、Sharpe、Sortino、Calmar 等）
- 基准对比（沪深300/中证500/创业板指/科创50）
- 参数优化能力（网格搜索、热力图）
- 走步验证（Walk-Forward）防止过拟合

**应该（SHOULD）**：
- 组合回测（多标的）
- 行业/相关性分析
- 一页式 Tearsheet 报告

### 1.2 非功能需求

- **性能**: 回测耗时 P95 ≤5s（3年日频数据，单策略）
- **可复现性**: 记录完整元数据（数据版本、参数、代码版本）
- **可扩展性**:
  - 易于添加新市场（通过三层配置：市场基础 + 板块规则 + 渠道规则）
  - 易于添加新的交易规则和指标
  - 无需修改核心代码
- **可测试性**: 核心逻辑单元测试覆盖率 ≥80%
- **多市场支持**: 详见 [多市场交易规则架构设计](./multi_market_trading_rules_design.md)

---

## 2. 现状分析与差距

### 2.1 现有实现

**文件**: `backend/app/services/backtest_service.py`

**已实现功能**：
- ✅ 基础状态机（持仓/空仓）
- ✅ 简单买卖信号（1=买, -1=卖, 0=持有）
- ✅ 手续费计算（比例+最低费用）
- ✅ 基础指标（总收益、胜率、最大回撤、盈亏比）
- ✅ 交易记录与权益曲线

**架构特点**：
- 单文件服务类（`BacktestService`）
- 逐行遍历数据框（for loop）
- 直接操作价格数据，无规则验证层
- 使用收盘价成交（无滑点）

### 2.2 功能差距

| 功能模块 | 现状 | 需求 | 优先级 |
|---------|------|------|--------|
| **交易规则** |
| T+1 制度 | ❌ 无 | ✅ 必须 | P0 |
| 涨跌停约束 | ❌ 无 | ✅ 必须 | P0 |
| 停牌处理 | ❌ 无 | ✅ 必须 | P0 |
| 集合竞价 | ❌ 无 | 🔶 可选 | P2 |
| **成本模型** |
| 手续费 | ✅ 有 | ✅ 增强 | P0 |
| 滑点 | ❌ 无 | ✅ 必须 | P0 |
| 撮合逻辑 | ❌ 无 | ✅ 必须 | P0 |
| 印花税 | ❌ 无 | ✅ 必须 | P1 |
| **性能指标** |
| 年化收益（CAGR） | ❌ 无 | ✅ 必须 | P0 |
| Sharpe 比率 | ❌ 无 | ✅ 必须 | P0 |
| Sortino 比率 | ❌ 无 | ✅ 必须 | P0 |
| Calmar 比率 | ❌ 无 | ✅ 必须 | P0 |
| 换手率 | ❌ 无 | ✅ 必须 | P1 |
| 仓位暴露 | ❌ 无 | ✅ 必须 | P1 |
| 基准对比 | ❌ 无 | ✅ 必须 | P0 |
| **优化与验证** |
| 参数网格搜索 | ❌ 无 | ✅ 必须 | P1 |
| 热力图可视化 | ❌ 无 | ✅ 必须 | P1 |
| 走步验证 | ❌ 无 | ✅ 必须 | P1 |
| **可复现性** |
| 元数据记录 | ❌ 无 | ✅ 必须 | P0 |
| 版本控制 | ❌ 无 | ✅ 必须 | P1 |

### 2.3 架构问题

1. **单一职责违反**: `BacktestService` 混合了交易逻辑、指标计算、数据处理
2. **规则硬编码**: 交易规则内嵌在循环中，难以扩展
3. **无撮合层**: 直接使用收盘价，无价格验证
4. **无风控层**: 缺少止损止盈、仓位限制等
5. **测试困难**: 紧耦合导致单元测试困难

---

## 3. 总体架构设计

### 3.1 分层架构

采用**分层 + 插件化**架构，提升可扩展性和可测试性：

```
┌──────────────────────────────────────────────────────────┐
│                     API Layer                             │
│  /api/v1/backtest, /api/v1/optimize, /api/v1/walk_forward│
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│                 Backtest Orchestrator                     │
│  - 协调各模块                                              │
│  - 元数据管理                                              │
│  - 结果聚合                                                │
└────────┬──────────┬──────────┬──────────┬────────────────┘
         │          │          │          │
    ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼─────────┐
    │ Trading│ │Matching│ │ Risk   │ │ Metrics    │
    │ Engine │ │ Engine │ │ Manager│ │ Calculator │
    │        │ │        │ │        │ │            │
    └────┬───┘ └───┬────┘ └───┬────┘ └──┬─────────┘
         │         │          │          │
    ┌────▼─────────▼──────────▼──────────▼─────────┐
    │          Trading Rules Validator              │
    │  - T+1 规则                                    │
    │  - 涨跌停约束                                  │
    │  - 停牌检查                                    │
    │  - 复权处理                                    │
    └──────────────────┬────────────────────────────┘
                       │
              ┌────────▼──────────┐
              │   Data Service    │
              │  - 行情数据        │
              │  - 交易日历        │
              │  - 标的状态        │
              └───────────────────┘
```

### 3.2 核心模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **API Layer** | 请求处理、参数验证、响应格式化 | HTTP Request | JSON Response |
| **Backtest Orchestrator** | 协调执行、元数据管理、结果聚合 | 回测配置 | 完整结果 |
| **Trading Engine** | 状态机、订单管理、持仓跟踪 | 信号+数据 | 订单序列 |
| **Matching Engine** | 撮合成交、滑点计算、价格验证 | 订单+行情 | 成交记录 |
| **Risk Manager** | 止损止盈、仓位限制、风险检查 | 持仓+订单 | 风控决策 |
| **Metrics Calculator** | 性能指标、基准对比、统计分析 | 交易+权益 | 指标字典 |
| **Trading Rules Validator** | **多市场三层架构**交易规则验证（见[架构设计](./multi_market_trading_rules_design.md)） | 订单+状态 | 通过/拒绝 |

### 3.3 设计原则

1. **单一职责**: 每个模块只负责一个领域
2. **开闭原则**: 规则和策略可插拔
3. **依赖倒置**: 面向接口编程，便于测试
4. **组合优于继承**: 使用组合构建复杂行为
5. **不可变性**: 核心数据结构不可变，避免副作用

---

## 4. 核心模块设计

### 4.1 Trading Engine（交易引擎）

**职责**: 管理交易状态机，生成订单

**核心类**: `TradingEngine`

```python
class TradingEngine:
    """交易引擎 - 管理持仓状态和订单生成"""

    def __init__(self, initial_capital: float):
        self.capital = initial_capital
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        self.orders: List[Order] = []
        self.trades: List[Trade] = []

    def process_signal(
        self,
        signal: Signal,
        market_data: MarketData,
        current_date: datetime
    ) -> Optional[Order]:
        """处理交易信号，生成订单"""
        pass

    def update_position(self, trade: Trade) -> None:
        """更新持仓状态"""
        pass

    def get_current_equity(self, market_prices: Dict[str, float]) -> float:
        """计算当前总权益"""
        pass
```

**状态机设计**:

```
           ┌─────────┐
           │  IDLE   │ (空仓)
           └────┬────┘
                │ 买入信号
           ┌────▼────────┐
           │ BUY_PENDING │
           └────┬────────┘
                │ T+1 约束检查
           ┌────▼────┐
           │ HOLDING │ (持仓)
           └────┬────┘
                │ 卖出信号
           ┌────▼─────────┐
           │ SELL_PENDING │
           └────┬─────────┘
                │ 执行卖出
           ┌────▼────┐
           │  IDLE   │
           └─────────┘
```

**T+1 实现**:
- 买入当日标记 `buy_date`
- 卖出信号触发时检查 `current_date > buy_date`
- 不满足条件的卖出信号延迟到次日

### 4.2 Matching Engine（撮合引擎）

**职责**: 模拟真实撮合，计算成交价格和滑点

**核心类**: `MatchingEngine`

```python
class MatchingEngine:
    """撮合引擎 - 模拟交易所撮合逻辑"""

    def __init__(self, slippage_bps: float = 5.0):
        self.slippage_bps = slippage_bps

    def match_order(
        self,
        order: Order,
        market_data: MarketData,
        rules_context: RulesContext
    ) -> Optional[Trade]:
        """撮合订单，返回成交记录"""
        # 1. 检查停牌
        if market_data.is_suspended:
            return None

        # 2. 检查涨跌停
        if not self._check_price_limit(order, market_data, rules_context):
            return None

        # 3. 计算滑点后价格
        execution_price = self._apply_slippage(order, market_data)

        # 4. 生成成交记录
        return Trade(...)

    def _check_price_limit(self, order: Order, data: MarketData, ctx: RulesContext) -> bool:
        """检查涨跌停限制"""
        if order.side == OrderSide.BUY:
            # 买入：价格不能超过涨停价
            limit_price = ctx.get_upper_limit(data.prev_close, data.board_type)
            return data.close < limit_price or not data.is_limit_up
        else:
            # 卖出：价格不能低于跌停价
            limit_price = ctx.get_lower_limit(data.prev_close, data.board_type)
            return data.close > limit_price or not data.is_limit_down

    def _apply_slippage(self, order: Order, data: MarketData) -> float:
        """应用滑点"""
        base_price = data.close
        if order.side == OrderSide.BUY:
            # 买入：向上滑点
            return base_price * (1 + self.slippage_bps / 10000)
        else:
            # 卖出：向下滑点
            return base_price * (1 - self.slippage_bps / 10000)
```

**涨跌停规则**:

| 板块 | 涨幅限制 | 跌幅限制 | 备注 |
|------|---------|---------|------|
| 主板（沪深） | +10% | -10% | 上证 6xxxxx，深证 000xxx |
| 创业板 | +20% | -20% | 深证 300xxx |
| 科创板 | +20% | -20% | 上证 688xxx |
| ST 股票 | +5% | -5% | 名称含 ST/\*ST |
| 北交所 | +30% | -30% | 43xxxx, 83xxxx, 87xxxx |

**涨跌停计算公式**:
```python
def get_price_limits(prev_close: float, board_type: str) -> Tuple[float, float]:
    """计算涨跌停价格"""
    limit_pct = {
        'MAIN': 0.10,      # 主板
        'GEM': 0.20,       # 创业板
        'STAR': 0.20,      # 科创板
        'ST': 0.05,        # ST
        'BSE': 0.30        # 北交所
    }[board_type]

    upper_limit = round(prev_close * (1 + limit_pct), 2)
    lower_limit = round(prev_close * (1 - limit_pct), 2)

    return upper_limit, lower_limit
```

### 4.3 Risk Manager（风控管理器）

**职责**: 执行风险控制规则

**核心类**: `RiskManager`

```python
class RiskManager:
    """风险管理器"""

    def __init__(self, config: RiskConfig):
        self.config = config

    def check_order(
        self,
        order: Order,
        portfolio: Portfolio,
        market_data: MarketData
    ) -> RiskCheckResult:
        """检查订单是否符合风控要求"""
        checks = [
            self._check_position_limit(order, portfolio),
            self._check_stop_loss(order, portfolio, market_data),
            self._check_stop_profit(order, portfolio, market_data),
            self._check_max_drawdown(portfolio),
        ]

        failed = [c for c in checks if not c.passed]
        return RiskCheckResult(
            passed=len(failed) == 0,
            reasons=[c.reason for c in failed]
        )

    def _check_position_limit(self, order: Order, portfolio: Portfolio) -> CheckItem:
        """检查仓位限制"""
        if order.side == OrderSide.BUY:
            position_value = order.quantity * order.limit_price
            total_value = portfolio.total_equity
            position_pct = position_value / total_value

            if position_pct > self.config.max_position_pct:
                return CheckItem(
                    passed=False,
                    reason=f"单票仓位 {position_pct:.1%} 超过限制 {self.config.max_position_pct:.1%}"
                )
        return CheckItem(passed=True)

    def _check_stop_loss(self, order: Order, portfolio: Portfolio, data: MarketData) -> CheckItem:
        """检查止损"""
        if order.side == OrderSide.SELL:
            position = portfolio.positions.get(order.symbol)
            if position:
                current_price = data.close
                loss_pct = (current_price - position.avg_cost) / position.avg_cost

                if loss_pct <= -self.config.stop_loss_pct:
                    # 触发止损，强制卖出
                    return CheckItem(passed=True, reason="触发止损")
        return CheckItem(passed=True)
```

**风控配置**:

```python
@dataclass
class RiskConfig:
    """风控配置"""
    max_position_pct: float = 0.3          # 单票最大仓位 30%
    stop_loss_pct: float = 0.1             # 止损线 10%
    stop_profit_pct: Optional[float] = None # 止盈线（可选）
    max_drawdown_pct: float = 0.2          # 最大回撤 20%
    max_leverage: float = 1.0              # 最大杠杆（现货=1）
```

### 4.4 Metrics Calculator（指标计算器）

**职责**: 计算性能指标和风险度量

**核心类**: `MetricsCalculator`

```python
class MetricsCalculator:
    """性能指标计算器"""

    @staticmethod
    def calculate_all_metrics(
        equity_curve: pd.Series,
        trades: List[Trade],
        benchmark_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.03
    ) -> Dict[str, float]:
        """计算所有性能指标"""
        returns = equity_curve.pct_change().dropna()

        metrics = {
            # 收益指标
            'total_return': MetricsCalculator.total_return(equity_curve),
            'cagr': MetricsCalculator.cagr(equity_curve),
            'annual_return': MetricsCalculator.annual_return(returns),

            # 风险指标
            'volatility': MetricsCalculator.volatility(returns),
            'max_drawdown': MetricsCalculator.max_drawdown(equity_curve),
            'max_drawdown_duration': MetricsCalculator.max_drawdown_duration(equity_curve),

            # 风险调整收益
            'sharpe_ratio': MetricsCalculator.sharpe_ratio(returns, risk_free_rate),
            'sortino_ratio': MetricsCalculator.sortino_ratio(returns, risk_free_rate),
            'calmar_ratio': MetricsCalculator.calmar_ratio(equity_curve),

            # 交易统计
            'total_trades': len([t for t in trades if t.side == TradeSide.BUY]),
            'win_rate': MetricsCalculator.win_rate(trades),
            'profit_factor': MetricsCalculator.profit_factor(trades),
            'avg_trade_return': MetricsCalculator.avg_trade_return(trades),

            # 持仓统计
            'turnover_rate': MetricsCalculator.turnover_rate(trades, equity_curve),
            'avg_holding_period': MetricsCalculator.avg_holding_period(trades),
        }

        # 基准对比（如果提供）
        if benchmark_returns is not None:
            metrics.update({
                'alpha': MetricsCalculator.alpha(returns, benchmark_returns, risk_free_rate),
                'beta': MetricsCalculator.beta(returns, benchmark_returns),
                'information_ratio': MetricsCalculator.information_ratio(returns, benchmark_returns),
                'tracking_error': MetricsCalculator.tracking_error(returns, benchmark_returns),
            })

        return metrics
```

**核心指标公式**:

1. **年化收益率 (CAGR)**:
   ```python
   def cagr(equity_curve: pd.Series) -> float:
       """Compound Annual Growth Rate"""
       start_value = equity_curve.iloc[0]
       end_value = equity_curve.iloc[-1]
       num_years = len(equity_curve) / 252  # 假设252个交易日

       return (end_value / start_value) ** (1 / num_years) - 1
   ```

2. **Sharpe 比率**:
   ```python
   def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.03) -> float:
       """Sharpe Ratio = (年化收益 - 无风险利率) / 年化波动率"""
       excess_returns = returns - risk_free_rate / 252
       return np.sqrt(252) * excess_returns.mean() / returns.std()
   ```

3. **Sortino 比率**:
   ```python
   def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.03) -> float:
       """Sortino Ratio = (年化收益 - 无风险利率) / 下行波动率"""
       excess_returns = returns - risk_free_rate / 252
       downside_returns = returns[returns < 0]
       downside_std = downside_returns.std()

       return np.sqrt(252) * excess_returns.mean() / downside_std
   ```

4. **Calmar 比率**:
   ```python
   def calmar_ratio(equity_curve: pd.Series) -> float:
       """Calmar Ratio = 年化收益 / 最大回撤"""
       cagr_value = cagr(equity_curve)
       max_dd = max_drawdown(equity_curve)

       return cagr_value / abs(max_dd) if max_dd != 0 else float('inf')
   ```

5. **最大回撤**:
   ```python
   def max_drawdown(equity_curve: pd.Series) -> float:
       """Maximum Drawdown"""
       rolling_max = equity_curve.expanding().max()
       drawdown = (equity_curve - rolling_max) / rolling_max
       return drawdown.min()
   ```

6. **换手率**:
   ```python
   def turnover_rate(trades: List[Trade], equity_curve: pd.Series) -> float:
       """年化换手率 = (买入金额总和 + 卖出金额总和) / 2 / 平均资产 * 年化因子"""
       total_volume = sum([t.amount for t in trades])
       avg_equity = equity_curve.mean()
       num_years = len(equity_curve) / 252

       return (total_volume / 2) / avg_equity / num_years
   ```

### 4.5 Trading Rules Validator（规则验证器）

**重要**: 本模块采用**三层架构**（市场-板块-渠道），详细设计见 **[多市场交易规则架构设计](./multi_market_trading_rules_design.md)**

**设计概述**:

```
Trading Rules Validator (本引擎)
         │
         ├─→ TradingRulesFactory.get_rules(environment)
         │
         ├─→ 三层规则组合
         │     ├─ Layer 1: MarketBaseRules (市场基础规则)
         │     │            T+1/T+2、交易时段、基础费用
         │     │
         │     ├─ Layer 2: BoardRules (板块特定规则)
         │     │            涨跌停比例、新股规则、盘后交易
         │     │
         │     └─ Layer 3: ChannelRules (渠道规则，可选)
         │                  港股通额外费用、QDII限制
         │
         └─→ 配置文件驱动（分层）
                  ├─ config/markets/cn/base.yaml
                  ├─ config/markets/cn/boards/main.yaml
                  ├─ config/markets/cn/boards/gem.yaml
                  ├─ config/markets/cn/boards/star.yaml
                  └─ config/channels/connect.yaml
```

**核心概念**:

```python
@dataclass(frozen=True)
class TradingEnvironment:
    """交易环境：市场+板块+渠道的组合"""
    market: str    # CN, HK, US
    board: str     # MAIN, GEM, STAR, BSE
    channel: str   # DIRECT, CONNECT

# 示例
env1 = TradingEnvironment('CN', 'MAIN', 'DIRECT')     # A股主板
env2 = TradingEnvironment('CN', 'GEM', 'DIRECT')      # A股创业板
env3 = TradingEnvironment('HK', 'MAIN', 'CONNECT')    # 港股通
env4 = TradingEnvironment('HK', 'MAIN', 'DIRECT')     # 直接港股
```

**使用示例**:

```python
# 回测引擎中的使用
class BacktestOrchestrator:

    def __init__(self, config: BacktestConfig):
        # 识别交易环境（自动识别板块）
        self.environment = TradingEnvironment.from_symbol(
            config.symbol,
            hint={'channel': config.channel}  # 用户指定渠道
        )

        # 获取三层组合规则
        self.rules = TradingRulesFactory.get_rules(self.environment)

    def validate_and_match_order(self, order, market_data, portfolio, context):
        # 使用组合规则验证（自动应用三层）
        validation = self.rules.validate_order(order, market_data, portfolio, context)

        if not validation.is_valid:
            return None  # 订单被拒绝

        # 获取板块特定涨跌停
        price_limits = self.rules.get_price_limits(market_data.prev_close, market_data.stock_info)

        # 获取市场+渠道费用
        commission = self.rules.get_commission(order.amount, order.side, market_data.stock_info)

        # 撮合成交...
```

**支持的交易环境**:

| 交易环境 | Environment | 涨跌停 | 交割 | 渠道费用 | 状态 |
|---------|-------------|--------|------|---------|------|
| A股主板 | `CN_MAIN` | ±10% | T+1 | 标准 | ✅ MVP |
| A股创业板 | `CN_GEM` | ±20% | T+1 | 标准 | ✅ MVP |
| A股科创板 | `CN_STAR` | ±20% | T+1 | 标准 | ✅ MVP |
| A股北交所 | `CN_BSE` | ±30% | T+1 | 标准 | 🔶 未来 |
| 港股通 | `HK_MAIN_CONNECT` | 无 | T+2 | +货币兑换 | ✅ MVP |
| 直接港股 | `HK_MAIN_DIRECT` | 无 | T+2 | 港股标准 | 🔶 未来 |
| 美股 | `US_NYSE` | 无 | T+2 | 标准 | 🔶 未来 |

**关键特性**:

1. **三层清晰分离**: 市场基础规则 + 板块特定规则 + 渠道额外规则
2. **精确建模现实**: 准确表达港股通等混合场景
3. **配置高度复用**: 市场基础配置被所有板块共享
4. **自动板块识别**: 根据股票代码自动识别板块
5. **规则独立测试**: 每层规则可独立测试

**集成点**:

- **Matching Engine**: 调用 `rules.get_price_limits()` 检查板块涨跌停
- **Trading Engine**: 调用 `rules.validate_order()` 验证市场+板块+渠道规则
- **Commission Calculation**: 调用 `rules.get_commission()` 计算市场+渠道费用

**配置示例**:

```yaml
# config/markets/cn/boards/gem.yaml
board_id: GEM
board_name: 创业板
stock_code_pattern: '^30\d{4}$'

price_limits:
  default:
    up_limit_pct: 0.20      # ±20%
  ipo_exception:
    first_n_days: 5         # 前5日无涨跌停
    up_limit_pct: null

authorization_required: true
```

详细实现请参考: **[多市场交易规则架构设计](./multi_market_trading_rules_design.md)**

---

## 5. 数据模型设计

### 5.1 核心数据类

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List

class OrderSide(Enum):
    """订单方向"""
    BUY = 'buy'
    SELL = 'sell'

class OrderStatus(Enum):
    """订单状态"""
    PENDING = 'pending'     # 待成交
    FILLED = 'filled'       # 已成交
    REJECTED = 'rejected'   # 已拒绝
    CANCELED = 'canceled'   # 已撤销

@dataclass(frozen=True)
class Signal:
    """交易信号"""
    symbol: str
    date: datetime
    action: int  # 1=买入, -1=卖出, 0=持有
    price: float
    reason: Optional[str] = None

@dataclass
class Order:
    """订单"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    limit_price: float
    created_at: datetime
    status: OrderStatus = OrderStatus.PENDING

@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    amount: float
    commission: float
    slippage: float
    executed_at: datetime

@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    buy_date: datetime  # 用于 T+1 检查

@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    prev_close: float
    is_suspended: bool = False
    is_limit_up: bool = False
    is_limit_down: bool = False
    board_type: str = 'MAIN'

@dataclass
class BacktestConfig:
    """回测配置"""
    # 基础参数
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100000

    # 成本参数
    commission_rate: float = 0.0003      # 手续费率 0.03%
    min_commission: float = 5.0          # 最低手续费
    slippage_bps: float = 5.0            # 滑点 5bp
    stamp_tax_rate: float = 0.001        # 印花税 0.1% (仅卖出)

    # 风控参数
    risk_config: Optional[RiskConfig] = None

    # 基准对比
    benchmark: Optional[str] = 'CSI300'  # 沪深300

    # 元数据
    strategy_id: str = None
    strategy_params: dict = None
    data_version: str = None
    engine_version: str = '2.0'

@dataclass
class BacktestResult:
    """回测结果"""
    # 配置信息
    config: BacktestConfig

    # 交易记录
    trades: List[Trade]
    equity_curve: pd.DataFrame

    # 性能指标
    metrics: Dict[str, float]

    # 基准对比
    benchmark_metrics: Optional[Dict[str, float]] = None

    # 元数据
    metadata: Dict[str, Any] = None
    created_at: datetime = None
```

### 5.2 数据库 Schema（用于结果存储）

```sql
-- 回测记录表
CREATE TABLE backtest_runs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    strategy_id VARCHAR(50),
    symbol VARCHAR(20),
    start_date DATE,
    end_date DATE,
    initial_capital DECIMAL(15, 2),
    final_capital DECIMAL(15, 2),
    total_return DECIMAL(10, 4),
    cagr DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    config JSON,  -- 完整配置
    metrics JSON,  -- 所有指标
    metadata JSON,  -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_strategy (strategy_id)
);

-- 交易记录表
CREATE TABLE backtest_trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    backtest_id VARCHAR(36),
    trade_id VARCHAR(50),
    symbol VARCHAR(20),
    side ENUM('buy', 'sell'),
    quantity INT,
    price DECIMAL(10, 4),
    amount DECIMAL(15, 2),
    commission DECIMAL(10, 2),
    executed_at DATETIME,
    FOREIGN KEY (backtest_id) REFERENCES backtest_runs(id) ON DELETE CASCADE,
    INDEX idx_backtest (backtest_id)
);

-- 权益曲线表
CREATE TABLE backtest_equity_curve (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    backtest_id VARCHAR(36),
    date DATE,
    equity DECIMAL(15, 2),
    capital DECIMAL(15, 2),
    position_value DECIMAL(15, 2),
    FOREIGN KEY (backtest_id) REFERENCES backtest_runs(id) ON DELETE CASCADE,
    INDEX idx_backtest_date (backtest_id, date)
);
```

---

## 6. 接口设计

### 6.1 扩展 `/api/v1/backtest` 接口

**请求体**:

```json
{
  // 基础参数（已有）
  "symbol": "000001",
  "strategy_id": "ma_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "initial_capital": 100000,
  "commission_rate": 0.0003,
  "strategy_params": {
    "short_period": 10,
    "long_period": 60
  },

  // 新增：成本模型参数
  "slippage_bps": 5.0,
  "stamp_tax_rate": 0.001,
  "min_commission": 5.0,

  // 新增：风控参数
  "risk_controls": {
    "max_position_pct": 0.3,
    "stop_loss_pct": 0.1,
    "stop_profit_pct": 0.2,
    "max_drawdown_pct": 0.2
  },

  // 新增：基准对比
  "benchmark": "CSI300",  // 可选: CSI300, CSI500, GEM, STAR50

  // 新增：元数据记录
  "save_result": true,    // 是否保存结果到数据库
  "result_name": "MA策略测试v1"
}
```

**响应体** (扩展字段):

```json
{
  "success": true,
  "data": {
    // 已有字段
    "stock": {...},
    "strategy": {...},

    // 扩展：更多指标
    "results": {
      // 收益指标
      "initial_capital": 100000,
      "final_capital": 125000,
      "total_return": 25.0,
      "cagr": 18.5,
      "annual_return": 19.2,

      // 风险指标
      "volatility": 0.25,
      "max_drawdown": -15.2,
      "max_drawdown_duration_days": 45,

      // 风险调整收益
      "sharpe_ratio": 1.2,
      "sortino_ratio": 1.5,
      "calmar_ratio": 1.22,

      // 交易统计
      "total_trades": 15,
      "winning_trades": 9,
      "losing_trades": 6,
      "win_rate": 60.0,
      "profit_factor": 1.6,
      "avg_trade_return": 3.5,

      // 持仓统计
      "turnover_rate": 2.5,
      "avg_holding_period_days": 12,
      "max_position_exposure": 0.85
    },

    // 新增：基准对比
    "benchmark": {
      "symbol": "CSI300",
      "total_return": 12.0,
      "cagr": 10.5,
      "sharpe_ratio": 0.8,
      "max_drawdown": -18.5,
      "alpha": 8.0,
      "beta": 0.95,
      "information_ratio": 0.45,
      "tracking_error": 12.5
    },

    // 新增：元数据
    "metadata": {
      "backtest_id": "bt_2025111200001",
      "engine_version": "2.0",
      "data_version": "20251112",
      "execution_time_ms": 1250,
      "rules_applied": ["T+1", "price_limit", "suspension"]
    },

    // 已有字段
    "trades": [...],
    "equity_curve": [...],
    "klines": [...],
    "buy_points": [...],
    "sell_points": [...]
  }
}
```

### 6.2 新增接口

#### 6.2.1 参数优化接口

**`POST /api/v1/backtest/optimize`**

```json
{
  "symbol": "000001",
  "strategy_id": "ma_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "initial_capital": 100000,

  // 参数网格
  "param_grid": {
    "short_period": [5, 10, 15, 20],
    "long_period": [30, 60, 90, 120]
  },

  // 优化目标
  "optimization_metric": "sharpe_ratio",  // 或 calmar_ratio, total_return

  // 约束条件
  "constraints": {
    "min_sharpe": 1.0,
    "max_drawdown": -0.20
  }
}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "best_params": {
      "short_period": 10,
      "long_period": 60,
      "score": 1.25
    },
    "grid_results": [
      {
        "params": {"short_period": 5, "long_period": 30},
        "sharpe_ratio": 0.85,
        "total_return": 15.2,
        "max_drawdown": -18.5
      },
      // ... 更多结果
    ],
    "heatmap_data": {
      "x_values": [5, 10, 15, 20],
      "y_values": [30, 60, 90, 120],
      "z_values": [[0.85, 1.25, 0.95, 0.75], ...]  // Sharpe ratio matrix
    }
  }
}
```

#### 6.2.2 走步验证接口

**`POST /api/v1/backtest/walk_forward`**

```json
{
  "symbol": "000001",
  "strategy_id": "ma_cross",
  "start_date": "20200101",
  "end_date": "20241231",
  "strategy_params": {
    "short_period": 10,
    "long_period": 60
  },

  // 走步配置
  "walk_forward_config": {
    "train_period_months": 12,
    "test_period_months": 3,
    "step_months": 3,
    "optimize_in_train": true,
    "optimization_metric": "sharpe_ratio"
  }
}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "periods": [
      {
        "period_id": 1,
        "train_start": "20200101",
        "train_end": "20201231",
        "test_start": "20210101",
        "test_end": "20210331",
        "train_metrics": {"sharpe_ratio": 1.2, ...},
        "test_metrics": {"sharpe_ratio": 0.95, ...},
        "best_params": {"short_period": 10, "long_period": 60}
      },
      // ... 更多时段
    ],
    "overall_metrics": {
      "avg_train_sharpe": 1.15,
      "avg_test_sharpe": 0.85,
      "degradation": 0.30,  // 测试集相比训练集的衰减
      "is_overfitting": true
    }
  }
}
```

---

## 7. 技术实现细节

### 7.1 交易日历集成

**数据源**: AkShare `tool_trade_date_hist_sina()`

```python
class TradingCalendar:
    """交易日历"""

    def __init__(self):
        self._cache = {}
        self._load_calendar()

    def _load_calendar(self):
        """加载交易日历"""
        df = ak.tool_trade_date_hist_sina()
        self.trading_days = set(pd.to_datetime(df['trade_date']))

    def is_trading_day(self, date: datetime) -> bool:
        """判断是否为交易日"""
        return date in self.trading_days

    def next_trading_day(self, date: datetime) -> datetime:
        """获取下一个交易日"""
        next_date = date + timedelta(days=1)
        while next_date not in self.trading_days:
            next_date += timedelta(days=1)
        return next_date

    def get_trading_days_between(self, start: datetime, end: datetime) -> List[datetime]:
        """获取日期区间内的所有交易日"""
        return sorted([d for d in self.trading_days if start <= d <= end])
```

### 7.2 板块与规则映射

```python
# 配置文件: config/trading_rules.yaml
trading_rules:
  price_limits:
    MAIN:
      up_limit: 0.10
      down_limit: 0.10
    GEM:
      up_limit: 0.20
      down_limit: 0.20
    STAR:
      up_limit: 0.20
      down_limit: 0.20
    ST:
      up_limit: 0.05
      down_limit: 0.05
    BSE:
      up_limit: 0.30
      down_limit: 0.30

  commission:
    default_rate: 0.0003
    min_commission: 5.0

  stamp_tax:
    rate: 0.001  # 仅卖出时收取

  settlement:
    t_plus_n: 1  # T+1
```

### 7.3 停牌检测

**方法1**: 基于成交量（简单但不完全准确）
```python
def detect_suspension_by_volume(df: pd.DataFrame) -> pd.Series:
    """基于成交量检测停牌"""
    return df['volume'] == 0
```

**方法2**: 使用 AkShare 停牌数据（更准确）
```python
def get_suspension_dates(symbol: str, start_date: str, end_date: str) -> Set[datetime]:
    """获取停牌日期"""
    # AkShare 提供停牌复牌数据
    df_suspension = ak.stock_stop_suspend(symbol=symbol)
    # 解析停牌期间
    suspension_dates = set()
    for _, row in df_suspension.iterrows():
        start = pd.to_datetime(row['停牌时间'])
        end = pd.to_datetime(row['复牌时间'])
        suspension_dates.update(pd.date_range(start, end))
    return suspension_dates
```

### 7.4 复权处理

确保数据一致性：

```python
def ensure_adjust_consistency(df: pd.DataFrame, adjust_type: str = 'qfq') -> pd.DataFrame:
    """确保复权一致性"""
    # 检查是否已复权
    if 'adjust_flag' in df.columns and df['adjust_flag'].iloc[0] == adjust_type:
        return df

    # 重新获取复权数据
    # （在实际使用中，应该从缓存的原始数据重新计算）
    return df
```

### 7.5 基准数据获取

```python
class BenchmarkService:
    """基准数据服务"""

    BENCHMARK_MAP = {
        'CSI300': '000300',    # 沪深300
        'CSI500': '000905',    # 中证500
        'GEM': '399006',       # 创业板指
        'STAR50': '000688',    # 科创50
    }

    @classmethod
    def get_benchmark_data(cls, benchmark_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取基准指数数据"""
        symbol = cls.BENCHMARK_MAP.get(benchmark_id)
        if not symbol:
            raise ValueError(f"Unknown benchmark: {benchmark_id}")

        df = ak.stock_zh_index_daily(symbol=symbol)
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        return df
```

---

## 8. 性能优化方案

### 8.1 计算优化

1. **向量化操作**: 使用 pandas/numpy 向量化替代循环
   ```python
   # 不推荐：循环
   for i in range(len(df)):
       df.loc[i, 'return'] = df.loc[i, 'close'] / df.loc[i-1, 'close'] - 1

   # 推荐：向量化
   df['return'] = df['close'].pct_change()
   ```

2. **懒计算**: 只在需要时计算指标
   ```python
   @property
   @lru_cache(maxsize=1)
   def sharpe_ratio(self):
       """缓存计算结果"""
       return self._calculate_sharpe()
   ```

3. **并行回测**: 参数网格搜索使用多进程
   ```python
   from concurrent.futures import ProcessPoolExecutor

   def optimize_parallel(param_grid):
       with ProcessPoolExecutor(max_workers=4) as executor:
           futures = [executor.submit(run_backtest, params) for params in param_grid]
           results = [f.result() for f in futures]
       return results
   ```

### 8.2 数据缓存

```python
class DataCacheManager:
    """数据缓存管理器"""

    def __init__(self, cache_dir: str = 'data/cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_or_fetch(self, key: str, fetch_func, ttl_hours: int = 24) -> Any:
        """获取缓存或重新获取"""
        cache_file = self.cache_dir / f"{key}.pkl"

        if cache_file.exists():
            # 检查缓存时效
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - cache_time < timedelta(hours=ttl_hours):
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)

        # 缓存失效或不存在，重新获取
        data = fetch_func()
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

        return data
```

### 8.3 性能监控

```python
import time
from functools import wraps

def timing_decorator(func):
    """性能计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        logger.info(f"{func.__name__} executed in {elapsed:.3f}s")

        # 记录到监控系统
        metrics.histogram('backtest.execution_time', elapsed, tags=[f'function:{func.__name__}'])

        return result
    return wrapper
```

---

## 9. 测试策略

### 9.1 单元测试

**测试覆盖范围**:

1. **Trading Rules Validator**
   - T+1 规则边界测试（当日买入尝试当日卖出）
   - 涨跌停判断（各板块）
   - 停牌检测
   - ST 股票识别

2. **Matching Engine**
   - 滑点计算
   - 涨停无法买入
   - 跌停无法卖出
   - 价格精度

3. **Metrics Calculator**
   - 各指标计算精度
   - 边界情况（零交易、全亏、全赚）
   - 基准对比计算

4. **Risk Manager**
   - 仓位限制
   - 止损触发
   - 止盈触发
   - 回撤保护

**示例测试**:

```python
# tests/test_trading_rules.py
import pytest
from datetime import datetime

def test_t_plus_1_restriction():
    """测试 T+1 限制"""
    validator = TradingRulesValidator(calendar)

    # 当日买入
    buy_date = datetime(2024, 1, 15)
    portfolio = Portfolio()
    portfolio.add_position(Position(
        symbol='000001',
        quantity=100,
        avg_cost=10.0,
        buy_date=buy_date
    ))

    # 尝试当日卖出
    sell_order = Order(
        symbol='000001',
        side=OrderSide.SELL,
        quantity=100,
        limit_price=10.5
    )

    result = validator._validate_t_plus_1(sell_order, portfolio, buy_date)

    assert result.is_valid == False
    assert 'T+1' in result.error_message

    # 次日卖出应该通过
    next_day = calendar.next_trading_day(buy_date)
    result = validator._validate_t_plus_1(sell_order, portfolio, next_day)
    assert result.is_valid == True

def test_price_limit_by_board():
    """测试不同板块涨跌停"""
    test_cases = [
        ('600000', 'MAIN', 10.0, 11.0, 9.0),    # 主板 ±10%
        ('300001', 'GEM', 20.0, 24.0, 16.0),    # 创业板 ±20%
        ('688001', 'STAR', 50.0, 60.0, 40.0),   # 科创板 ±20%
    ]

    for symbol, board, prev_close, expected_upper, expected_lower in test_cases:
        upper, lower = get_price_limits(prev_close, board)
        assert abs(upper - expected_upper) < 0.01
        assert abs(lower - expected_lower) < 0.01
```

### 9.2 集成测试

```python
# tests/test_backtest_integration.py

def test_complete_backtest_flow():
    """测试完整回测流程"""
    config = BacktestConfig(
        symbol='000001',
        start_date='20230101',
        end_date='20231231',
        initial_capital=100000,
        commission_rate=0.0003,
        slippage_bps=5.0
    )

    # 准备数据
    df = DataService.get_stock_data('000001', '20230101', '20231231')
    df = IndicatorService.calculate_all_indicators(df)
    df = StrategyService.apply_strategy('ma_cross', df, {'short': 10, 'long': 60})

    # 运行回测
    orchestrator = BacktestOrchestrator(config)
    result = orchestrator.run(df)

    # 验证结果
    assert result is not None
    assert 'metrics' in result
    assert result['metrics']['total_trades'] >= 0
    assert result['metrics']['final_capital'] > 0

    # 验证 T+1 规则
    trades = result['trades']
    buy_trades = {t for t in trades if t.side == TradeSide.BUY}
    sell_trades = {t for t in trades if t.side == TradeSide.SELL}

    for sell in sell_trades:
        corresponding_buy = next(b for b in buy_trades if b.symbol == sell.symbol)
        assert sell.executed_at.date() > corresponding_buy.executed_at.date()
```

### 9.3 回测不变式测试

```python
def test_backtest_invariants():
    """测试回测不变式"""
    result = run_backtest(config)

    # 不变式1: 有成本后收益不应优于无成本
    result_no_cost = run_backtest(config_with_zero_costs)
    assert result['final_capital'] <= result_no_cost['final_capital']

    # 不变式2: 最大回撤不应为正
    assert result['metrics']['max_drawdown'] <= 0

    # 不变式3: 权益曲线长度应等于交易日数量
    trading_days = calendar.get_trading_days_between(start_date, end_date)
    assert len(result['equity_curve']) == len(trading_days)

    # 不变式4: 买入金额 + 手续费不应超过可用资金
    for trade in result['trades']:
        if trade.side == TradeSide.BUY:
            total_cost = trade.amount + trade.commission
            # 需要追踪每笔交易时的可用资金
            assert total_cost <= trade.available_capital
```

### 9.4 性能测试

```python
def test_backtest_performance():
    """测试回测性能"""
    config = BacktestConfig(
        symbol='000001',
        start_date='20210101',  # 3年数据
        end_date='20231231',
        initial_capital=100000
    )

    import time
    start = time.time()
    result = run_backtest(config)
    elapsed = time.time() - start

    # P95 目标 ≤5s
    assert elapsed < 5.0, f"Backtest took {elapsed:.2f}s, exceeds 5s target"
```

---

## 10. 风险与挑战

### 10.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 数据源变更 | 高 | 中 | 抽象数据层，易于切换数据源 |
| 性能下降 | 中 | 中 | 性能测试，缓存，并行化 |
| 规则复杂度 | 中 | 高 | 插件化设计，单元测试覆盖 |

### 10.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 回测结果不可信 | 高 | 中 | 严格的规则验证，对照真实交易 |
| 过拟合误导 | 高 | 高 | 走步验证，多时段测试 |
| 规则理解偏差 | 中 | 中 | 文档详尽，与券商规则对标 |

### 10.3 挑战

1. **涨跌停撮合精确性**
   - 挑战：封板时是否成交难以精确模拟
   - 方案：保守假设（涨停不可买入，跌停不可卖出）

2. **滑点建模**
   - 挑战：滑点受流动性、订单大小影响
   - 方案：简化模型（固定 bp），后续可引入动态滑点

3. **停牌数据完整性**
   - 挑战：AkShare 停牌数据可能不完整
   - 方案：结合成交量判断，提供手动标注接口

4. **基准数据对齐**
   - 挑战：指数数据与个股数据日期可能不对齐
   - 方案：使用交易日历对齐，缺失数据前向填充

---

## 11. 开发计划

### 11.1 Day 1-2: 核心架构搭建

**任务**:
- ✅ 创建模块结构（`app/backtest/`）
- ✅ 定义数据模型（`models.py`）
- ✅ 实现交易日历（`trading_calendar.py`）
- ✅ 实现板块分类器（`board_classifier.py`）

**交付物**:
- 可运行的模块骨架
- 基础数据类定义
- 单元测试框架

### 11.2 Day 3-4: 规则验证器 + 撮合引擎

**任务**:
- ✅ 实现 `TradingRulesValidator`
  - T+1 规则
  - 涨跌停检查
  - 停牌检查
- ✅ 实现 `MatchingEngine`
  - 滑点计算
  - 价格验证
  - 成交记录生成
- ✅ 单元测试（覆盖率 >80%）

**交付物**:
- 完整的规则验证模块
- 完整的撮合引擎
- 测试报告

### 11.3 Day 5-6: 交易引擎 + 指标计算

**任务**:
- ✅ 实现 `TradingEngine`
  - 状态机
  - 订单生成
  - 持仓管理
- ✅ 实现 `MetricsCalculator`
  - 所有性能指标
  - 基准对比
- ✅ 集成测试

**交付物**:
- 完整的交易引擎
- 完整的指标计算器
- 端到端测试通过

### 11.4 Day 7-8: 编排器 + API 集成

**任务**:
- ✅ 实现 `BacktestOrchestrator`
- ✅ 扩展 API 接口
- ✅ 元数据记录
- ✅ 集成测试

**交付物**:
- 完整的回测流程
- API 文档更新
- 集成测试通过

### 11.5 Day 9-10: 优化功能 + 测试

**任务**:
- ✅ 实现参数网格搜索
- ✅ 实现走步验证（可选，P1）
- ✅ 性能优化
- ✅ 完整的端到端测试
- ✅ 文档编写

**交付物**:
- 优化功能完成
- 性能达标（P95 <5s）
- 用户文档 + API 文档

### 11.6 Day 11-12: 集成 + 部署

**任务**:
- ✅ 前端适配（显示新指标）
- ✅ 数据库 migration
- ✅ Docker 构建
- ✅ 灰度发布

**交付物**:
- 完整的端到端系统
- 部署文档
- 监控配置

---

## 12. 附录

### 12.1 目录结构

```
backend/
├── app/
│   ├── backtest/              # 回测引擎
│   │   ├── __init__.py
│   │   ├── models.py          # 数据模型
│   │   ├── orchestrator.py    # 编排器
│   │   ├── trading_engine.py  # 交易引擎
│   │   ├── matching_engine.py # 撮合引擎
│   │   ├── risk_manager.py    # 风控管理器
│   │   ├── metrics.py         # 指标计算
│   │   ├── rules/             # 规则模块
│   │   │   ├── __init__.py
│   │   │   ├── validator.py   # 规则验证器
│   │   │   ├── calendar.py    # 交易日历
│   │   │   └── classifier.py  # 板块分类
│   │   └── optimization/      # 优化模块
│   │       ├── grid_search.py
│   │       └── walk_forward.py
│   ├── api/v1/
│   │   ├── backtest.py        # 回测接口
│   │   └── optimize.py        # 优化接口
│   └── services/
│       ├── backtest_service.py  # 当前简单服务（待升级）
│       └── benchmark_service.py # 基准数据服务
│
└── tests/
    ├── backtest/
    │   ├── test_trading_engine.py
    │   ├── test_matching_engine.py
    │   ├── test_rules_validator.py
    │   ├── test_metrics.py
    │   └── test_integration.py
    └── fixtures/
        └── sample_data.py
```

### 12.2 参考资料

- **A股交易规则**: [上交所交易规则](http://www.sse.com.cn/)
- **技术指标**: [QuantLib](https://www.quantlib.org/)
- **回测框架参考**: Backtrader, Zipline, VectorBT
- **风险指标**: [Portfolio Performance Measurement](https://en.wikipedia.org/wiki/Portfolio_performance_measurement)

---

**文档维护**:
- 每次设计变更需更新本文档
- 代码实现后补充实际 API 示例
- 测试完成后补充性能数据

**审核记录**:
- [ ] 技术 Leader 审核
- [ ] 产品经理审核
- [ ] QA 审核

---
