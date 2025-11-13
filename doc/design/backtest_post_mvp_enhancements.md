# 回测引擎后续增强设计文档

**版本**: v1.0
**创建时间**: 2025-11-12
**状态**: 设计中
**关联文档**:
- PRD: `doc/requirements/product_requirements_stock_pal.md`
- 引擎升级设计: `doc/design/backtest_engine_upgrade_design.md`

---

## 1. 概述

### 1.1 背景

回测引擎2.0核心功能已完成（100%），但PRD中"可信回测（MUST）"部分还有2个必备功能未实现：
1. 风控管理器（Risk Manager）
2. 基准对比API集成

此外，还有一些产品功能和代码质量优化项。

### 1.2 优先级分级

| 优先级 | 类型 | 功能 | PRD要求 | 影响 |
|-------|------|------|---------|------|
| **P0** | 必备功能 | 风控管理器 | MUST | 阻塞PRD验收 |
| **P0** | 必备功能 | 基准对比API | MUST | 阻塞PRD验收 |
| **P1** | 产品功能 | 数据库持久化 | SHOULD | 影响用户体验 |
| **P2** | 代码质量 | 配置文件系统 | - | 提升可维护性 |
| **P3** | 产品路线图 | 多市场扩展 | Future | 未来规划 |

---

## 2. P0：风控管理器（Risk Manager）

### 2.1 需求来源

**PRD章节**：
- 4.1 必备一：可信回测（MUST） - "风险模块（止损/止盈/回撤保护）"
- 4.3 必备三：风险与"地雷"过滤（MUST） - "策略级风控：单票/组合止损止盈、最大回撤阈值、仓位上限"

### 2.2 功能范围

#### 核心风控规则

| 规则类型 | 说明 | 触发条件 | 动作 |
|---------|------|---------|------|
| **仓位限制** | 单票最大仓位 | 买入订单导致持仓>阈值 | 拒绝订单 |
| **止损** | 个股止损 | 当前价格 < 成本 * (1 - 止损%) | 强制卖出 |
| **止盈** | 个股止盈 | 当前价格 > 成本 * (1 + 止盈%) | 强制卖出 |
| **回撤保护** | 组合回撤保护 | 当前权益 < 最高权益 * (1 - 最大回撤%) | 清仓 |
| **波动率目标** | 波动率控制 | 组合波动率 > 目标波动率 | 降低仓位 |

#### 配置结构

```python
@dataclass
class RiskConfig:
    # 仓位控制
    max_position_pct: float = 0.3          # 单票最大仓位 30%
    max_total_exposure: float = 0.95       # 最大总仓位 95%

    # 止损止盈
    stop_loss_pct: Optional[float] = None  # 止损线（如0.1表示-10%）
    stop_profit_pct: Optional[float] = None # 止盈线（如0.2表示+20%）

    # 组合风控
    max_drawdown_pct: float = 0.2          # 最大回撤保护 20%
    volatility_target: Optional[float] = None # 目标波动率

    # 其他
    max_leverage: float = 1.0              # 最大杠杆（现货=1）
    enable_trailing_stop: bool = False     # 是否启用移动止损
```

### 2.3 架构设计

#### 集成点

```
TradingEngine.process_bar()
    │
    ├─→ 1. 检查卖出信号
    ├─→ 2. RiskManager.check_exit_signals()  【新增】
    │       └─→ 止损/止盈/回撤保护检查 → 生成强制卖出订单
    │
    ├─→ 3. 检查买入信号
    └─→ 4. RiskManager.check_order_risk()    【新增】
            └─→ 仓位限制检查 → 通过/拒绝订单
```

#### 模块职责

- **RiskManager**:
  - 输入：Portfolio状态、Order、MarketData
  - 输出：RiskCheckResult（通过/拒绝/强制卖出）

- **TradingEngine**:
  - 在买入前调用风控检查
  - 在每日循环开始时检查退出信号

### 2.4 关键实现点

1. **止损/止盈优先级高于策略信号**：风控模块可以强制生成卖出订单
2. **回撤保护基于运行时最高权益**：需要实时跟踪peak_equity
3. **波动率目标需要滚动计算**：使用最近N日的收益率标准差
4. **风控拒绝需要记录**：在Metadata中记录被拒绝的订单和原因

### 2.5 测试要点

- 止损触发正确性（临界值测试）
- 仓位限制边界测试
- 回撤保护触发验证
- 风控与策略信号的优先级
- 多重风控规则同时触发的处理

---

## 3. P0：基准对比API集成

### 3.1 需求来源

**PRD章节**：
- 4.1 必备一：可信回测（MUST） - "基准对比（沪深300/中证500/创业板指/科创50）"
- 7. API设计草案 - 回测返回示例中包含 `"benchmark"` 字段

### 3.2 功能范围

#### 基准指标

| 指标 | 说明 | 用途 |
|------|------|------|
| **Alpha** | 策略超额收益 | 衡量策略的选股能力 |
| **Beta** | 系统风险暴露 | 衡量策略与市场的相关性 |
| **Information Ratio** | 信息比率 | 超额收益的稳定性 |
| **Tracking Error** | 跟踪误差 | 策略偏离基准的程度 |
| **基准权益曲线** | 基准指数的收益走势 | 对比可视化 |

#### 支持的基准

| 基准代码 | 名称 | 说明 |
|---------|------|------|
| `CSI300` | 沪深300 | 大盘蓝筹 |
| `CSI500` | 中证500 | 中盘成长 |
| `GEM` | 创业板指 | 创业板综合 |
| `STAR50` | 科创50 | 科创板龙头 |

### 3.3 架构设计

#### 数据流

```
API Request (benchmark="CSI300")
    │
    ├─→ BenchmarkService.get_benchmark_data()
    │       └─→ 从AkShare获取指数数据
    │
    ├─→ BacktestOrchestrator.run()
    │       ├─→ 策略回测 → strategy_returns
    │       └─→ MetricsCalculator.calculate_all_metrics(benchmark_returns)
    │
    └─→ API Response
            ├─→ results.alpha
            ├─→ results.beta
            ├─→ benchmark.equity_curve
            └─→ benchmark.metrics
```

#### 新增服务

- **BenchmarkService** (`app/services/benchmark_service.py`):
  - 缓存基准数据（避免重复请求）
  - 处理日期对齐（基准和股票数据的交易日可能不完全一致）
  - 计算基准收益率

### 3.4 API变更

#### 请求增强

```json
POST /api/v1/backtest
{
  "symbol": "600000",
  "strategy_id": "ma_cross",
  "start_date": "20220101",
  "end_date": "20241231",
  "benchmark": "CSI300"  // 新增字段
}
```

#### 响应增强

```json
{
  "results": {
    // 原有指标...
    "alpha": 0.08,        // 新增
    "beta": 0.95,         // 新增
    "information_ratio": 0.45,  // 新增
    "tracking_error": 0.12      // 新增
  },
  "benchmark": {          // 新增整个字段
    "symbol": "CSI300",
    "total_return": 0.12,
    "cagr": 0.10,
    "sharpe_ratio": 0.8,
    "max_drawdown": -0.18,
    "equity_curve": [...]
  }
}
```

### 3.5 前端显示

在 BacktestPage 新增第5个 MetricsCard：

```
📊 基准对比
├─ Alpha（超额收益）
├─ Beta（系统风险）
├─ 信息比率
└─ 跟踪误差
```

在权益曲线图中叠加基准曲线（双Y轴）。

### 3.6 关键实现点

1. **日期对齐**：基准和策略的日期范围可能不完全一致，需要取交集
2. **数据缓存**：基准数据按日期范围缓存，避免重复请求
3. **收益率计算**：确保基准和策略使用相同的收益率计算方式
4. **可选字段**：benchmark参数为空时不进行基准对比

---

## 4. P1：数据库持久化

### 4.1 需求来源

**PRD章节**：
- 8. 前端页面 - "Backtests：历史回测列表、对比与导出"

### 4.2 功能范围

- 保存回测结果到数据库
- 查询历史回测记录
- 对比多次回测结果
- 导出回测报告

### 4.3 数据库设计

核心表（参考 backtest_engine_upgrade_design.md 第5.2节）：
- `backtest_runs`：回测记录主表
- `backtest_trades`：交易明细
- `backtest_equity_curve`：权益曲线

### 4.4 新增API

- `GET /api/v1/backtests`：获取历史回测列表
- `GET /api/v1/backtests/{id}`：获取单个回测详情
- `DELETE /api/v1/backtests/{id}`：删除回测记录
- `POST /api/v1/backtests/compare`：对比多个回测

---

## 5. P2：配置文件系统

### 5.1 需求来源

**设计文档**：multi_market_trading_rules_design.md - 三层配置架构

### 5.2 功能范围

将硬编码的交易规则迁移到YAML配置文件：

```
config/
├── markets/
│   └── cn/
│       ├── base.yaml        # T+1、交易时段、基础费用
│       └── boards/
│           ├── main.yaml    # 主板：±10%
│           ├── gem.yaml     # 创业板：±20%
│           ├── star.yaml    # 科创板：±20%
│           └── st.yaml      # ST：±5%
└── channels/
    ├── direct.yaml          # 直接交易
    └── connect.yaml         # 港股通
```

### 5.3 优势

- 规则修改无需重启服务
- 易于扩展新市场/板块
- 配置集中管理
- 支持多环境配置（开发/生产）

### 5.4 迁移策略

1. 先创建配置文件（与现有硬编码保持一致）
2. 实现配置加载器
3. 逐步替换硬编码
4. 保持单元测试通过
5. 删除旧代码

---

## 6. P3：多市场扩展

### 6.1 范围

- 港股通完整支持（T+0交易、T+2资金交割、货币兑换费）
- 直接港股交易
- 美股交易规则

### 6.2 前置条件

- P2 配置文件系统完成
- 数据源支持（AkShare港股/美股数据）

### 6.3 工作内容

- 完善港股/美股的TradingRules配置
- 扩展SymbolClassifier支持港股/美股代码
- 测试不同市场的回测准确性

---

## 7. 实施建议

### 7.1 推荐顺序

1. **Week 1**: P0 - 风控管理器（完成PRD必备功能）
2. **Week 1**: P0 - 基准对比API集成（完成PRD必备功能）
3. **Week 2**: P1 - 数据库持久化（提升产品体验）
4. **Week 3**: P2 - 配置文件系统（提升代码质量）
5. **Future**: P3 - 多市场扩展（产品路线图）

### 7.2 验收标准

#### P0 风控管理器
- [ ] 单票仓位限制生效
- [ ] 止损/止盈正确触发
- [ ] 回撤保护正确触发
- [ ] 风控配置可通过API传入
- [ ] 单元测试覆盖各风控规则

#### P0 基准对比
- [ ] API返回Alpha/Beta/IR/TE
- [ ] API返回基准权益曲线
- [ ] 前端显示基准对比指标
- [ ] 前端图表叠加基准曲线
- [ ] 支持4种基准指数

#### P1 数据库持久化
- [ ] 回测结果自动保存
- [ ] 历史回测列表可查询
- [ ] 回测详情可查看
- [ ] 多次回测可对比

---

## 8. 风险与注意事项

### 8.1 风控管理器

**风险**：
- 风控规则与策略信号的优先级冲突
- 回撤保护可能过度敏感导致提前退出
- 止损/止盈阈值设置不当影响收益

**对策**：
- 明确风控优先级高于策略信号
- 风控参数可配置，支持关闭
- 提供风控影响分析（对比有/无风控的结果）

### 8.2 基准对比

**风险**：
- 基准数据缺失或延迟
- 日期不对齐导致指标计算错误

**对策**：
- 缓存基准数据，失败时优雅降级
- 严格的日期对齐逻辑
- 单元测试覆盖边界情况

### 8.3 数据库持久化

**风险**：
- 数据量增长过快
- 查询性能问题

**对策**：
- 定期清理旧数据（保留策略）
- 索引优化
- 分页查询

---

## 9. 相关文档

- PRD: `doc/requirements/product_requirements_stock_pal.md`
- 回测引擎设计: `doc/design/backtest_engine_upgrade_design.md`
- 多市场规则设计: `doc/design/multi_market_trading_rules_design.md`
- 前端增强设计: `doc/design/frontend_metrics_enhancement_design.md`
- 开发进度: `doc/progress/backtest_engine_upgrade_progress.md`

---

**文档状态**: ✅ 已完成
**下一步**: 按优先级开始实施
