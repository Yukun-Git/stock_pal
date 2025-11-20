# 单股多策略分析功能 - Brainstorm 记录

**日期**: 2025-11-19
**参与者**: 用户 + Claude
**相关文档**: `doc/backlog/单股多策略实时分析.md`

---

## 📋 会议摘要

对原始backlog文档进行了深入讨论，明确了功能定位、技术方案和UI设计。核心决策：将功能定位为**策略探索和筛选工具**，帮助用户从所有策略中发现适合的交易机会，并引导进入深度回测。

---

## 🎯 核心定位确认

### 问题：场景A vs 场景B？

**场景A：决策辅助工具**（单股深度分析）
```
用户：我看中了贵州茅台，现在能买吗？
系统：展示所有策略的信号和历史表现
用户：MA交叉和MACD都不错，我去回测页深入研究一下
```

**场景B：机会扫描工具**（批量扫描）
```
用户：我有100只自选股，哪些现在有买点？
系统：筛选出5只有2个以上买入信号的股票
```

### ✅ 决策：选择场景A

**理由**：
- 用户已有关注的股票（自选股）
- 需要深度了解单只股票的交易机会
- 策略间的分歧是有价值的信息，不应隐藏
- 引导用户进入回测页进行深度分析

**定位调整**：
- ❌ 不是"告诉你该不该买"（决策建议）
- ✅ 而是"展示所有可能的交易角度，帮你选出感兴趣的策略"（策略探索）

**用户旅程**：
```
1. 我关注这只股票（自选股）
   ↓
2. 用所有策略扫一遍，看看有哪些机会（多策略分析页）
   ↓
3. 某个策略看起来不错，深入研究（回测页）
   ↓
4. 调参数、看历史表现、验证可靠性（参数优化）
```

---

## 📊 功能设计决策

### 1. 策略卡片增强 - 添加回测曲线

**用户需求**：
> "我希望每个策略都展示一条回测收益率曲线（时间段默认最后一年），这样用户可以快速浏览、比较不同策略在过去一段时间内的回测表现"

**卡片结构**（最终版）：

```
┌─────────────────────────────────────────────────┐
│ 🟢 MA交叉策略                    [快速回测]    │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📈 过去一年表现 (2024-01-01 ~ 2024-11-17)      │
│                                                 │
│    ┌─────────────────────────────────┐         │
│    │         /\      /\              │         │
│    │        /  \    /  \    /\       │ 110k    │
│    │   /\  /    \  /    \  /  \      │         │
│    │  /  \/      \/      \/    \     │         │
│    │ ─────────────────────────────── │ 100k    │
│    │ 1月  3月  6月  9月  11月        │         │
│    └─────────────────────────────────┘         │
│                                                 │
│ 收益率: +23.5%  最大回撤: -8.2%  夏普: 1.8    │
│ 交易次数: 12次  胜率: 66.7%                    │
│                                                 │
├─────────────────────────────────────────────────┤
│ 当前状态                                        │
│ • 信号: 🟢 买入 (5天前, ¥12.50)                │
│ • 如果执行: 浮盈 +6.7% (¥12.50 → ¥13.34)      │
│ • 关键指标: MA5: 13.2, MA20: 12.8              │
├─────────────────────────────────────────────────┤
│ [查看完整回测] [调整参数] [策略说明]          │
└─────────────────────────────────────────────────┘
```

**卡片分区比例**：
- **历史表现** (60%): 迷你曲线图 + 关键指标
- **当前状态** (40%): 最新信号 + 浮盈浮亏 + 技术指标
- **操作按钮**: 引导进入回测页

**价值**：
- 用户能看到策略的真实历史表现，而不只是"当前信号"
- 增加信任度：如果策略过去一年收益不佳，用户会谨慎对待
- 快速对比：不用逐个进回测页，就能比较多个策略

---

### 2. 迷你图表技术选型

**✅ 决策：使用 ECharts 折线图**

**方案对比**：

| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| ECharts折线图 | 功能完整、交互好、可定制 | 体积稍大 | ✅ 选择 |
| Sparkline | 极简、不占空间 | 信息密度低、无交互 | ❌ |

**ECharts配置**：
```typescript
const miniChartOption = {
  grid: { left: 10, right: 10, top: 10, bottom: 20 },
  xAxis: {
    type: 'category',
    data: dates,
    axisLabel: { fontSize: 10 }
  },
  yAxis: {
    type: 'value',
    axisLabel: { show: false },
    splitLine: { lineStyle: { type: 'dashed' } }
  },
  series: [{
    type: 'line',
    data: equityData,
    smooth: true,
    lineStyle: { width: 2, color: '#52c41a' },
    areaStyle: { /* 渐变色 */ },
    symbol: 'none'
  }],
  tooltip: { /* 悬停显示详情 */ }
};
```

**图表尺寸**：
- 宽度：100%（充满卡片）
- 高度：150px

---

### 3. 性能优化方案

**✅ 决策：数据共享 + 异步加载 + 简化回测**

**问题**：6个策略 × 1年回测 = 可能很慢

**优化方案**：

#### 方案1：数据和指标共享
```python
def analyze_with_mini_backtests(symbol, strategies):
    # 1. 获取数据（一次）- 1秒
    df = get_stock_data(symbol, start='2024-01-01', end='2024-11-17')

    # 2. 计算所有指标（一次）- 1秒
    df = calculate_all_indicators(df)

    # 3. 并行运行回测
    for strategy in strategies:  # 6个策略
        signals = strategy.generate_signals(df.copy(), default_params)
        equity_curve = calculate_equity_curve_fast(df, signals)
        metrics = calculate_basic_metrics(equity_curve)

    # 总耗时：1 + 1 + (0.1 × 6) = 2.6秒 ✅
```

**关键点**：
- 数据只获取一次（节省 1-2秒/策略）
- 指标只计算一次（节省 0.5-1秒/策略）
- 简化回测：不需要完整交易明细，只要权益曲线

#### 方案2：异步加载（如果仍然慢）
```typescript
// 第一阶段：快速加载信号（1秒）
fetchCurrentSignals(symbol).then(signals => {
  setStrategies(signals);  // 先显示信号部分
});

// 第二阶段：异步加载回测曲线（2-3秒）
fetchMiniBacktests(symbol).then(backtests => {
  setStrategies(prev => mergeBacktestData(prev, backtests));
});
```

**用户体验时间轴**：
- 0秒: 用户点击"分析"
- 1秒: 显示所有策略的信号状态（骨架屏+信号灯）
- 3秒: 图表逐个加载完成

---

### 4. 策略排序

**✅ 决策：默认按类型分组**

**分组方式**：

```
┌─ 📈 趋势类策略 (3个) ──────────────────────┐
│  MA交叉    MACD金叉    EMA交叉            │
└──────────────────────────────────────────┘

┌─ 📊 超买超卖策略 (3个) ────────────────────┐
│  KDJ交叉   RSI反转    布林带突破          │
└──────────────────────────────────────────┘

┌─ 🕯️ 形态识别策略 (2个) ────────────────────┐
│  早晨之星  黄昏之星                        │
└──────────────────────────────────────────┘
```

**可选排序**（未来扩展）：
- 按收益率排序
- 按信号类型排序（买入优先）
- 按夏普比率排序

**理由**：
- 帮助用户理解"不同类型策略关注点不同"
- 分歧不是矛盾，而是"多角度观察"
- 引导用户思考：我是趋势交易者还是短线交易者？

---

### 5. 对比视图设计

**✅ 决策：只显示收益最好的6个策略**

**问题**：如果支持20+策略，所有曲线叠加会太乱

**对比视图设计**：

```
┌─────────────────────────────────────────────────┐
│ [卡片视图] [对比视图]                           │
└─────────────────────────────────────────────────┘

对比视图（Top 6）：

┌─────────────────────────────────────────────────┐
│ 📈 收益最高的6个策略对比                        │
├─────────────────────────────────────────────────┤
│                                                 │
│ 120k ┼                                          │
│      │         ╱ MA交叉 (绿色) +23.5%          │
│ 115k ┼      ╱                                   │
│      │   ╱─── MACD (蓝色) +18.3%               │
│ 110k ┼ ╱                                        │
│      │╱─────── 布林带 (橙色) +12.7%            │
│ 105k ┼───────── RSI (紫色) +8.1%               │
│      │                                          │
│ 100k ┼─────────────────────────────────────    │
│      1月   3月   6月   9月   11月              │
└─────────────────────────────────────────────────┘

策略排名：
1. MA交叉:     +23.5%  回撤 -8.2%  夏普 1.8  ⭐️
2. MACD金叉:   +18.3%  回撤 -12.5% 夏普 1.2
3. 布林突破:   +12.7%  回撤 -6.1%  夏普 1.5
4. RSI反转:    +8.1%   回撤 -9.2%  夏普 0.9
5. EMA交叉:    +6.3%   回撤 -7.8%  夏普 0.7
6. KDJ交叉:    +2.1%   回撤 -15.3% 夏普 0.2

[查看全部策略排名]
```

**筛选逻辑**：
```python
# 按收益率排序，取前6个
top_strategies = sorted(strategies, key=lambda s: s.backtest.total_return, reverse=True)[:6]
```

**价值**：
- 避免图表过于拥挤
- 突出表现最好的策略
- 如果用户想看全部，提供"展开"选项

---

## 🎨 UI/UX 设计决策

### 页面命名

**建议改名**：
- ❌ "单股多策略实时分析"（太像决策工具）
- ✅ "策略扫描" / "策略雷达" / "策略对比"

**Slogan**：
> 一键查看所有策略在该股票上的信号，找到最适合的交易机会

---

### 页面结构

```
┌─────────────────────────────────────────────────┐
│ 🔍 股票代码: [600519] [分析]                   │
│ 回测时间:    [3个月] [6个月] [1年▼] [2年] [全部]│
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 贵州茅台 (600519)    当前价: ¥1,680            │
│ 数据截止: 2025-11-17 收盘                      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 📈 趋势类策略 (3个)                             │
├─────────────────────────────────────────────────┤
│ [MA交叉卡片]  [MACD金叉卡片]  [EMA交叉卡片]   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 📊 超买超卖策略 (3个)                           │
├─────────────────────────────────────────────────┤
│ [KDJ卡片]  [RSI卡片]  [布林带卡片]            │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 🕯️ 形态识别策略 (2个)                          │
├─────────────────────────────────────────────────┤
│ [早晨之星卡片]  [黄昏之星卡片]                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 💡 策略分歧分析                                 │
├─────────────────────────────────────────────────┤
│ • 趋势类策略：3/3 看涨（平均收益 +18.2%）     │
│ • 超买超卖类：2/3 看跌（平均收益 -2.1%）      │
│ • 形态识别：无明确信号                         │
│                                                 │
│ 分析结论：趋势向上但短期过热。激进者可小仓位  │
│ 建仓，稳健者等待回调结束。                     │
└─────────────────────────────────────────────────┘
```

---

### 引导用户进入回测页

**设计思路**：降低从"看"到"试"的门槛

**按钮设计**：
```
┌─────────────────────────────────────┐
│ [快速回测] [调整参数] [策略详情]   │
└─────────────────────────────────────┘
```

**交互流程**：

1. **点击"快速回测"**：
   - 自动填充：symbol + strategy_id + 默认参数
   - 跳转到回测页
   - 回测页自动执行一次快速回测
   - 展示完整结果（交易明细、权益曲线、指标）

2. **点击"调整参数"**：
   - 跳转到回测页
   - 参数区域自动展开
   - 高亮提示："试试调整这些参数，看看效果变化"

3. **点击"策略详情"**：
   - 打开侧边栏/弹窗
   - 展示策略原理、适用场景、参数说明

---

### 策略分歧的展示

**核心原则**：不隐藏分歧，而是解释分歧

**分歧分析文本生成逻辑**：
```python
def generate_divergence_analysis(strategies):
    # 按类型分组统计
    trend_signals = [s for s in strategies if s.category == 'trend']
    osc_signals = [s for s in strategies if s.category == 'oscillator']

    trend_buy = sum(1 for s in trend_signals if s.signal == 'buy')
    osc_sell = sum(1 for s in osc_signals if s.signal == 'sell')

    if trend_buy > 0 and osc_sell > 0:
        return (
            "趋势类策略看涨，但超买超卖类策略提示短期过热。"
            "这种分歧说明：可能是上涨趋势中的短期回调，"
            "激进者可小仓位建仓，稳健者等待回调结束。"
        )
    # ... 其他情况
```

**关键**：不是简单投票（3:2买入胜），而是**解释为什么会分歧**。

---

## 🔧 技术实现要点

### API设计

**端点**：
```
POST /api/v1/stocks/multi-strategy-analysis
```

**请求参数**：
```json
{
  "symbol": "600519",
  "lookback_days": 365,  // 回测时间（天）
  "end_date": "2024-11-17"  // 可选，默认最新
}
```

**响应结构**：
```json
{
  "symbol": "600519",
  "symbol_name": "贵州茅台",
  "current_price": 1680.00,
  "analysis_date": "2024-11-17",
  "data_range": {
    "start": "2024-01-01",
    "end": "2024-11-17"
  },
  "strategies": [
    {
      "strategy_id": "ma_cross",
      "strategy_name": "MA交叉",
      "category": "trend",

      // 历史表现
      "backtest": {
        "equity_curve": [
          { "date": "2024-01-01", "equity": 100000 },
          { "date": "2024-01-02", "equity": 100350 }
        ],
        "metrics": {
          "total_return": 0.235,
          "max_drawdown": -0.082,
          "sharpe_ratio": 1.8,
          "total_trades": 12,
          "win_rate": 0.667
        }
      },

      // 当前状态
      "current_signal": {
        "type": "buy",
        "triggered_date": "2024-11-12",
        "triggered_price": 12.50,
        "days_ago": 5,
        "current_pnl": 0.067,
        "still_valid": true
      },

      // 关键指标
      "indicators": {
        "ma5": 13.2,
        "ma20": 12.8
      }
    }
  ],
  "summary": {
    "signal_distribution": {
      "buy": 2,
      "sell": 1,
      "hold": 3
    },
    "avg_return": 0.156,
    "best_strategy": "ma_cross",
    "worst_strategy": "kdj_cross"
  }
}
```

---

### 核心服务层

```python
class MultiStrategyAnalysisService:
    """多策略分析服务"""

    def analyze_stock(self, symbol: str, lookback_days: int = 365):
        """
        用所有策略分析单只股票

        Returns:
            包含所有策略分析结果的字典
        """
        # 1. 获取数据（一次）
        df = self.data_service.get_stock_data(
            symbol,
            lookback=lookback_days
        )

        # 2. 计算所有指标（一次）
        df = self.indicator_service.calculate_all_indicators(df)

        # 3. 遍历所有策略
        results = []
        for strategy_cls in StrategyRegistry.get_all():
            strategy = strategy_cls()

            # 运行迷你回测
            analysis = self._run_mini_backtest(df, strategy)
            results.append(analysis)

        # 4. 生成综合分析
        summary = self._generate_summary(results)

        return {
            'strategies': results,
            'summary': summary
        }

    def _run_mini_backtest(self, df, strategy):
        """运行简化版回测（只计算权益曲线）"""
        params = strategy.get_default_params()

        # 生成信号
        df_signals = strategy.generate_signals(df.copy(), params)

        # 计算权益曲线（简化版，不需要完整交易明细）
        equity_curve = self._calculate_equity_curve_fast(df_signals)

        # 计算关键指标
        metrics = self._calculate_basic_metrics(equity_curve)

        # 分析最后的信号
        current_signal = self._analyze_last_signal(df_signals)

        # 提取关键技术指标
        indicators = self._extract_key_indicators(df_signals, strategy)

        return {
            'strategy': strategy,
            'backtest': {
                'equity_curve': equity_curve,
                'metrics': metrics
            },
            'current_signal': current_signal,
            'indicators': indicators
        }
```

---

### 前端组件结构

```typescript
// 页面组件
const StrategyAnalysisPage = () => {
  const [symbol, setSymbol] = useState('600519');
  const [timeRange, setTimeRange] = useState(365); // 天数
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    const result = await api.analyzeStock(symbol, timeRange);
    setStrategies(result.strategies);
    setLoading(false);
  };

  return (
    <div>
      <SearchBar
        symbol={symbol}
        onSymbolChange={setSymbol}
        onAnalyze={handleAnalyze}
      />

      <TimeRangeSelector
        value={timeRange}
        onChange={setTimeRange}
        options={[90, 180, 365, 730]}
      />

      {loading ? (
        <SkeletonCards count={6} />
      ) : (
        <>
          <StrategyGroup title="趋势类策略" category="trend">
            {strategies
              .filter(s => s.category === 'trend')
              .map(s => <StrategyCard key={s.id} strategy={s} />)}
          </StrategyGroup>

          <StrategyGroup title="超买超卖策略" category="oscillator">
            {strategies
              .filter(s => s.category === 'oscillator')
              .map(s => <StrategyCard key={s.id} strategy={s} />)}
          </StrategyGroup>

          <DivergenceAnalysis strategies={strategies} />
        </>
      )}
    </div>
  );
};

// 策略卡片组件
const StrategyCard = ({ strategy }) => {
  return (
    <Card>
      <CardHeader>
        <SignalBadge type={strategy.current_signal.type} />
        <StrategyName>{strategy.strategy_name}</StrategyName>
      </CardHeader>

      <PerformanceSection>
        <MiniChart
          data={strategy.backtest.equity_curve}
          height={150}
        />
        <MetricsGrid metrics={strategy.backtest.metrics} />
      </PerformanceSection>

      <CurrentStatusSection signal={strategy.current_signal} />

      <CardFooter>
        <Button onClick={() => gotoFullBacktest(strategy)}>
          查看完整回测
        </Button>
        <Button onClick={() => gotoBacktestWithParams(strategy)}>
          调整参数
        </Button>
      </CardFooter>
    </Card>
  );
};

// 迷你图表组件
const MiniChart = ({ data, height }) => {
  const chartRef = useRef(null);

  useEffect(() => {
    const chart = echarts.init(chartRef.current);

    const option = {
      grid: { left: 10, right: 10, top: 10, bottom: 20 },
      xAxis: {
        type: 'category',
        data: data.map(d => d.date),
        axisLabel: { fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        axisLabel: { show: false }
      },
      series: [{
        type: 'line',
        data: data.map(d => d.equity),
        smooth: true,
        lineStyle: { width: 2, color: '#52c41a' },
        areaStyle: { /* 渐变 */ }
      }],
      tooltip: { /* ... */ }
    };

    chart.setOption(option);

    return () => chart.dispose();
  }, [data]);

  return <div ref={chartRef} style={{ height }} />;
};
```

---

## 📋 MVP范围确认

### 必须实现（第一版）

1. ✅ 股票代码输入和验证
2. ✅ 时间范围选择（3个月/6个月/1年/2年）
3. ✅ 用所有策略分析（默认参数）
4. ✅ **每个策略显示迷你回测曲线（ECharts）**
5. ✅ **显示关键回测指标（收益、回撤、夏普、胜率）**
6. ✅ 显示当前信号状态（买入/卖出/观望）
7. ✅ 如果有信号，显示"如果执行"的浮盈浮亏
8. ✅ 按策略类型分组展示（趋势/超买超卖/形态）
9. ✅ 一键跳转到完整回测页（参数预填充）
10. ✅ 简单的策略分歧分析文本
11. ✅ 对比视图（收益最好的6个策略）

### 可选功能（看时间）

- 🤔 更详细的分歧分析（多维度对比）
- 🤔 策略适用性检查（该策略适不适合这只股票）
- 🤔 自定义排序（按收益/按信号/按夏普）

### 延后功能

- ⏸️ 信号强度评分（★★★☆☆）
- ⏸️ 参数自动优化
- ⏸️ "即将触发"预判
- ⏸️ 历史信号准确率统计
- ⏸️ 批量股票扫描（场景B）

---

## ⚠️ 风险与注意事项

### 1. 法律合规

**免责声明**（必须显示）：
```
⚠️ 重要提示：
1. 本分析基于历史数据和技术指标，仅供学习参考
2. 不构成任何投资建议或买卖股票的依据
3. 投资有风险，决策需谨慎，盈亏自负
4. 技术分析不保证未来收益
5. 请根据自身风险承受能力做出决策
```

**实施**：
- 用户首次使用时弹窗确认
- 每个分析结果页面都显示简短提示

---

### 2. 数据时效性说明

**问题**：AkShare数据是T+1（昨日收盘后更新）

**解决方案**：
- 明确标注"数据截止时间"
- 添加提示："本分析基于历史数据"
- 避免使用"实时"这个词

**UI示例**：
```
┌─────────────────────────────────────────────┐
│ 贵州茅台 (600519)                           │
│ 数据截止: 2025-11-17 收盘                  │
│ 下次更新: 2025-11-18 收盘后               │
└─────────────────────────────────────────────┘
```

---

### 3. 用户过度依赖

**风险**：用户可能无脑跟单，亏了怪平台

**用户教育文案**：
```
💡 如何使用本功能：
1. 本功能是"辅助工具"，不是"自动交易机器人"
2. 信号仅代表技术面，需结合基本面、消息面综合判断
3. 建议：先在模拟盘或小仓位测试策略效果
4. 不同策略适合不同市场环境，学会判断市场状态
```

---

### 4. 性能监控

**需要监控的指标**：
- API响应时间（目标 < 3秒）
- 内存使用（多策略并行计算）
- 数据缓存命中率

**降级方案**：
- 如果数据获取失败，显示缓存数据
- 如果计算超时，先显示部分策略结果

---

## 🚀 实施计划

### 预估工作量：3-5天

**Day 1-2: 后端开发**
- [ ] 新增 `MultiStrategyAnalysisService`
- [ ] 实现 `_run_mini_backtest()` 简化回测逻辑
- [ ] 实现 `_analyze_last_signal()` 信号分析
- [ ] 新增 API 端点 `/api/v1/stocks/multi-strategy-analysis`
- [ ] 实现数据共享和性能优化
- [ ] 单元测试

**Day 3-4: 前端开发**
- [ ] 新增"策略扫描"页面
- [ ] 实现 `StrategyCard` 组件
- [ ] 集成 ECharts 迷你图表
- [ ] 实现策略分组展示
- [ ] 实现对比视图（Top 6）
- [ ] 实现跳转到回测页的逻辑

**Day 5: 测试与优化**
- [ ] 端到端测试
- [ ] 性能测试（响应时间）
- [ ] UI/UX 调整
- [ ] 添加免责声明和用户引导

---

## 📊 验收标准

### 功能验收

- [ ] 用户可以输入股票代码并获得分析结果
- [ ] 所有可用策略都参与分析（至少6个策略）
- [ ] 每个策略显示迷你回测曲线（过去1年）
- [ ] 每个策略显示关键指标：收益率、回撤、夏普、胜率
- [ ] 每个策略显示当前信号和浮盈浮亏
- [ ] 策略按类型分组展示
- [ ] 对比视图显示收益最好的6个策略
- [ ] 一键跳转到回测页功能正常
- [ ] 数据时间明确标注
- [ ] 免责声明已添加

### 性能验收

- [ ] API响应时间 < 3秒（6个策略）
- [ ] 前端首次渲染 < 1秒
- [ ] 图表加载流畅，无卡顿

### 用户体验验收

- [ ] 加载状态清晰（骨架屏/进度条）
- [ ] 失败策略正常展示（不隐藏）
- [ ] 跳转流程顺畅（参数自动填充）
- [ ] 移动端适配良好

---

## 🔗 相关文档

- 原始需求：`doc/backlog/单股多策略实时分析.md`
- 策略注册表：`backend/app/strategies/registry.py`
- 指标服务：`backend/app/services/indicator_service.py`
- 回测服务：`backend/app/backtest/orchestrator.py`

---

## 💡 后续优化方向

### 短期（1-2周后）

1. **添加排序功能**
   - 按收益率排序
   - 按信号类型排序
   - 按夏普比率排序

2. **策略适用性检查**
   - 基于股票特征判断策略是否适用
   - 显示适用性评分

3. **"即将触发"预判**
   - 检测指标是否接近阈值
   - 提示潜在机会

### 中期（1-2月后）

4. **历史信号统计**
   - 该策略过去30/60天的信号历史
   - 信号准确率统计

5. **参数自动优化**
   - 一键寻找该股票的最优参数
   - 显示优化前后对比

6. **批量扫描（场景B）**
   - 支持上传自选股列表
   - 筛选有明确信号的股票

### 长期（3月+）

7. **信号提醒与订阅**
   - 用户订阅关注股票
   - 触发信号时推送通知

8. **社区功能**
   - 分享分析结果
   - 查看其他用户关注的股票

---

**文档状态**: ✅ 已完成
**下一步**: 进入开发实施阶段
