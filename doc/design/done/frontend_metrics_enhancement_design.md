# 前端增强指标显示设计文档

**文档版本**: 1.0
**创建日期**: 2025-11-12
**设计目标**: 在前端显示回测引擎2.0的18种增强性能指标

---

## 1. 背景与目标

### 1.1 背景

回测引擎2.0已完成升级，新引擎提供了18种专业性能指标，包括：
- **收益指标**: 总收益率、年化收益率(CAGR)、年化收益
- **风险指标**: 波动率、最大回撤、最大回撤持续期
- **风险调整收益**: Sharpe比率、Sortino比率、Calmar比率
- **交易统计**: 胜率、盈亏比、平均交易收益率、平均持仓天数
- **持仓统计**: 换手率

### 1.2 目标

1. **完整展示**: 在前端界面显示所有18种指标
2. **用户友好**: 合理分组、清晰标注、专业解释
3. **向后兼容**: 不影响现有功能，平滑升级
4. **响应式设计**: 适配不同屏幕尺寸
5. **视觉优化**: 突出重要指标，使用颜色编码

---

## 2. 当前状态分析

### 2.1 现有指标显示

**位置**: `BacktestPage.tsx` 第660-729行

**当前显示的8个指标**:
```typescript
- 总收益率 (total_return)
- 最终资金 (final_capital)
- 交易次数 (total_trades)
- 胜率 (win_rate)
- 最大回撤 (max_drawdown)
- 盈利因子 (profit_factor)
- 平均盈利 (avg_profit)
- 平均亏损 (avg_loss)
```

**布局**: 使用 Ant Design `Statistic` 组件，8列网格布局

### 2.2 新增指标（10个）

后端已返回但前端未显示：
```typescript
1. cagr - 年化收益率 (%)
2. sharpe_ratio - 夏普比率
3. sortino_ratio - 索提诺比率
4. calmar_ratio - 卡玛比率
5. volatility - 波动率 (%)
6. max_drawdown_duration - 最大回撤持续期 (天)
7. turnover_rate - 换手率 (年化)
8. avg_holding_period - 平均持仓天数
9. avg_trade_return - 平均交易收益率 (%)
10. metadata - 元数据 (backtest_id, execution_time等)
```

---

## 3. 设计方案

### 3.1 指标分组策略

将18种指标分为**4个核心板块**，便于用户理解：

#### 📊 板块1: 收益指标 (Returns)
**目标**: 展示策略赚了多少钱

| 指标 | 字段 | 单位 | 说明 |
|------|------|------|------|
| 总收益率 | total_return | % | 整个回测期间的总收益 |
| 年化收益率 (CAGR) | cagr | % | 年化复合增长率 |
| 最终资金 | final_capital | ¥ | 回测结束时的资金 |
| 平均交易收益 | avg_trade_return | % | 每次交易的平均收益率 |

#### ⚠️ 板块2: 风险指标 (Risk)
**目标**: 展示策略有多风险

| 指标 | 字段 | 单位 | 说明 |
|------|------|------|------|
| 最大回撤 | max_drawdown | % | 最大亏损幅度 |
| 回撤持续期 | max_drawdown_duration | 天 | 最大回撤持续时间 |
| 波动率 | volatility | % | 收益波动程度（年化） |
| 换手率 | turnover_rate | - | 年化换手频率 |

#### 🎯 板块3: 风险调整收益 (Risk-Adjusted Returns)
**目标**: 综合考虑收益和风险

| 指标 | 字段 | 单位 | 说明 |
|------|------|------|------|
| Sharpe比率 | sharpe_ratio | - | 每单位风险的超额收益 |
| Sortino比率 | sortino_ratio | - | 考虑下行风险的收益比 |
| Calmar比率 | calmar_ratio | - | 年化收益/最大回撤 |
| 盈亏比 | profit_factor | - | 总盈利/总亏损 |

#### 📈 板块4: 交易统计 (Trading Statistics)
**目标**: 展示交易行为

| 指标 | 字段 | 单位 | 说明 |
|------|------|------|------|
| 交易次数 | total_trades | 次 | 总交易笔数 |
| 胜率 | win_rate | % | 盈利交易占比 |
| 平均持仓天数 | avg_holding_period | 天 | 每次交易平均持有时间 |
| 平均盈利/亏损 | avg_profit/avg_loss | ¥ | 单次盈亏金额 |

---

### 3.2 UI/UX设计

#### 3.2.1 布局方案

**方案A: 分组卡片布局** (推荐)

```
┌─────────────────────────────────────────────────────────┐
│  📊 回测结果总览                                          │
├─────────────────────────────────────────────────────────┤
│  📊 收益指标                                              │
│  ┌───────┬───────┬───────┬───────┐                      │
│  │总收益率│ CAGR │最终资金│平均收益│                      │
│  └───────┴───────┴───────┴───────┘                      │
├─────────────────────────────────────────────────────────┤
│  ⚠️ 风险指标                                              │
│  ┌───────┬───────┬───────┬───────┐                      │
│  │最大回撤│回撤期 │ 波动率 │ 换手率 │                      │
│  └───────┴───────┴───────┴───────┘                      │
├─────────────────────────────────────────────────────────┤
│  🎯 风险调整收益                                          │
│  ┌───────┬───────┬───────┬───────┐                      │
│  │ Sharpe│Sortino│Calmar │ 盈亏比 │                      │
│  └───────┴───────┴───────┴───────┘                      │
├─────────────────────────────────────────────────────────┤
│  📈 交易统计                                              │
│  ┌───────┬───────┬───────┬───────┐                      │
│  │交易次数│ 胜率  │持仓天数│平均盈亏│                      │
│  └───────┴───────┴───────┴───────┘                      │
└─────────────────────────────────────────────────────────┘
```

**方案B: Tabs标签页布局** (备选)

```
┌─────────────────────────────────────────────────────────┐
│  📊 回测结果                                              │
│  [收益指标] [风险指标] [风险调整] [交易统计]              │
├─────────────────────────────────────────────────────────┤
│  当前选中: 收益指标                                        │
│  ┌───────┬───────┬───────┬───────┐                      │
│  │总收益率│ CAGR │最终资金│平均收益│                      │
│  └───────┴───────┴───────┴───────┘                      │
└─────────────────────────────────────────────────────────┘
```

**推荐**: **方案A（分组卡片布局）**
- 优点: 一目了然，无需切换，便于对比
- 缺点: 占用垂直空间
- 适用场景: 专业用户需要同时查看多个指标

#### 3.2.2 颜色编码策略

| 指标类型 | 颜色规则 | 示例 |
|---------|---------|------|
| 收益率 | 正值红色，负值绿色 | +5.2% (红), -3.1% (绿) |
| 风险指标 | 值越大颜色越深（橙色系） | 低风险(浅橙), 高风险(深橙) |
| 比率指标 | >1 绿色, <1 橙色 | Sharpe 1.5 (绿), 0.8 (橙) |
| 计数指标 | 中性色（黑/灰） | 交易次数 15次 |

#### 3.2.3 Tooltip说明文案

每个指标都应提供清晰的Tooltip说明：

```typescript
const METRIC_TOOLTIPS = {
  cagr: "年化复合增长率，衡量策略的长期收益能力",
  sharpe_ratio: "夏普比率 = (年化收益 - 无风险利率) / 波动率。>1优秀，>2非常好",
  sortino_ratio: "索提诺比率，只考虑下行风险的收益指标，越高越好",
  calmar_ratio: "卡玛比率 = 年化收益 / 最大回撤，衡量单位回撤的收益，越高越好",
  volatility: "收益波动率（年化），衡量策略的稳定性，越低越稳定",
  max_drawdown_duration: "从最高点到恢复所需的最长时间",
  turnover_rate: "年化换手率，衡量策略的交易频率",
  avg_holding_period: "平均每次交易持有的天数",
  avg_trade_return: "每次交易的平均收益率",
};
```

---

### 3.3 响应式设计

#### 桌面端 (>= 1200px)
```tsx
<Row gutter={16}>
  <Col span={6}>指标1</Col>
  <Col span={6}>指标2</Col>
  <Col span={6}>指标3</Col>
  <Col span={6}>指标4</Col>
</Row>
```

#### 平板端 (768px - 1199px)
```tsx
<Row gutter={16}>
  <Col sm={12} md={12}>指标1</Col>
  <Col sm={12} md={12}>指标2</Col>
  <Col sm={12} md={12}>指标3</Col>
  <Col sm={12} md={12}>指标4</Col>
</Row>
```

#### 移动端 (< 768px)
```tsx
<Row gutter={16}>
  <Col xs={24}>指标1</Col>
  <Col xs={24}>指标2</Col>
  <Col xs={24}>指标3</Col>
  <Col xs={24}>指标4</Col>
</Row>
```

---

## 4. 技术实现方案

### 4.1 类型定义更新

**文件**: `frontend/src/types/index.ts`

```typescript
export interface BacktestResult {
  // ===== 基础指标（向后兼容）=====
  initial_capital: number;
  final_capital: number;
  total_return: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  max_drawdown: number;
  avg_profit: number;
  avg_loss: number;
  profit_factor: number;

  // ===== 新增增强指标 =====
  // 收益指标
  cagr: number;                      // 年化收益率

  // 风险指标
  volatility: number;                // 波动率（年化）
  max_drawdown_duration: number;     // 最大回撤持续期（天）

  // 风险调整收益
  sharpe_ratio: number;              // 夏普比率
  sortino_ratio: number;             // 索提诺比率
  calmar_ratio: number;              // 卡玛比率

  // 交易统计
  avg_trade_return: number;          // 平均交易收益率
  avg_holding_period: number;        // 平均持仓天数
  turnover_rate: number;             // 换手率（年化）
}

export interface BacktestMetadata {
  backtest_id: string;               // 回测唯一ID
  engine_version: string;            // 引擎版本
  execution_time_seconds: number;    // 执行时间（秒）
  environment?: string;              // 交易环境
  started_at?: string;               // 开始时间
}

export interface BacktestResponse {
  stock: Stock;
  strategy: string | {
    strategies: string[];
    combine_mode: string;
    vote_threshold?: number;
  };
  results: BacktestResult;
  trades: Trade[];
  equity_curve: EquityPoint[];
  klines: KLine[];
  buy_points: Array<{ date: string; price: number }>;
  sell_points: Array<{ date: string; price: number }>;
  signal_analysis?: SignalAnalysis;
  metadata?: BacktestMetadata;       // 新增：元数据
}
```

---

### 4.2 组件拆分

#### 4.2.1 创建指标卡片组件

**文件**: `frontend/src/components/MetricsCard.tsx`

```tsx
import { Card, Row, Col, Statistic, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';

interface MetricItem {
  title: string;
  value: number | string;
  precision?: number;
  prefix?: string;
  suffix?: string;
  valueStyle?: React.CSSProperties;
  tooltip?: string;
}

interface MetricsCardProps {
  title: string;
  icon?: string;
  metrics: MetricItem[];
  columns?: number; // 每行显示多少列（默认4）
}

export default function MetricsCard({
  title,
  icon,
  metrics,
  columns = 4
}: MetricsCardProps) {
  const span = 24 / columns;

  return (
    <Card title={`${icon || ''} ${title}`} style={{ marginTop: 24 }}>
      <Row gutter={16}>
        {metrics.map((metric, index) => (
          <Col xs={24} sm={12} md={span} key={index}>
            <Statistic
              title={
                <span>
                  {metric.title}
                  {metric.tooltip && (
                    <Tooltip title={metric.tooltip}>
                      <QuestionCircleOutlined
                        style={{ marginLeft: 4, color: '#8c8c8c' }}
                      />
                    </Tooltip>
                  )}
                </span>
              }
              value={metric.value}
              precision={metric.precision}
              prefix={metric.prefix}
              suffix={metric.suffix}
              valueStyle={metric.valueStyle}
            />
          </Col>
        ))}
      </Row>
    </Card>
  );
}
```

#### 4.2.2 创建指标配置

**文件**: `frontend/src/utils/metricsConfig.ts`

```typescript
export const METRIC_TOOLTIPS = {
  total_return: "整个回测期间的总收益率",
  cagr: "年化复合增长率，衡量策略的长期收益能力",
  final_capital: "回测结束时的总资金",
  avg_trade_return: "每次交易的平均收益率",

  max_drawdown: "从最高点到最低点的最大亏损幅度",
  max_drawdown_duration: "从最高点到恢复所需的最长时间（交易日）",
  volatility: "收益波动率（年化），越低越稳定",
  turnover_rate: "年化换手率，衡量交易频率",

  sharpe_ratio: "夏普比率 = (年化收益 - 无风险利率) / 波动率。>1优秀，>2非常好",
  sortino_ratio: "索提诺比率，只考虑下行风险，越高越好",
  calmar_ratio: "卡玛比率 = 年化收益 / 最大回撤，越高越好",
  profit_factor: "盈亏比 = 总盈利 / 总亏损，>1盈利，>2优秀",

  total_trades: "回测期间的总交易次数",
  win_rate: "盈利交易占总交易的比例",
  avg_holding_period: "平均每次交易持有的天数",
  avg_profit: "盈利交易的平均金额",
  avg_loss: "亏损交易的平均金额",
};

// 判断指标好坏的颜色逻辑
export function getMetricColor(metricName: string, value: number): string {
  // 收益类指标：正红负绿
  if (['total_return', 'cagr', 'avg_trade_return', 'avg_profit'].includes(metricName)) {
    return value >= 0 ? '#ff4d4f' : '#52c41a';
  }

  // 比率指标：>1好，<1差
  if (['sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'profit_factor'].includes(metricName)) {
    if (value >= 2) return '#52c41a';      // 绿色：优秀
    if (value >= 1) return '#faad14';      // 橙色：良好
    return '#ff4d4f';                       // 红色：较差
  }

  // 风险指标：值越大越危险
  if (['max_drawdown', 'volatility'].includes(metricName)) {
    if (Math.abs(value) > 20) return '#ff4d4f';  // 红色：高风险
    if (Math.abs(value) > 10) return '#faad14';  // 橙色：中风险
    return '#52c41a';                             // 绿色：低风险
  }

  // 默认黑色
  return '#262626';
}
```

---

### 4.3 BacktestPage改造

**文件**: `frontend/src/pages/BacktestPage.tsx`

**改动点**:

1. **导入新组件**:
```tsx
import MetricsCard from '@/components/MetricsCard';
import { METRIC_TOOLTIPS, getMetricColor } from '@/utils/metricsConfig';
```

2. **替换现有的Results Statistics卡片** (第660-730行):

```tsx
{/* 原有代码 */}
<Card title="📊 回测结果" style={{ marginTop: 24 }}>
  <Row gutter={16}>
    {/* 8个Statistic组件 */}
  </Row>
</Card>

{/* 改为 */}
{/* 📊 收益指标 */}
<MetricsCard
  title="收益指标"
  icon="📊"
  metrics={[
    {
      title: '总收益率',
      value: result.results.total_return,
      precision: 2,
      suffix: '%',
      valueStyle: { color: getMetricColor('total_return', result.results.total_return) },
      tooltip: METRIC_TOOLTIPS.total_return,
    },
    {
      title: '年化收益率 (CAGR)',
      value: result.results.cagr,
      precision: 2,
      suffix: '%',
      valueStyle: { color: getMetricColor('cagr', result.results.cagr) },
      tooltip: METRIC_TOOLTIPS.cagr,
    },
    {
      title: '最终资金',
      value: result.results.final_capital,
      precision: 2,
      prefix: '¥',
      tooltip: METRIC_TOOLTIPS.final_capital,
    },
    {
      title: '平均交易收益',
      value: result.results.avg_trade_return || 0,
      precision: 2,
      suffix: '%',
      valueStyle: { color: getMetricColor('avg_trade_return', result.results.avg_trade_return || 0) },
      tooltip: METRIC_TOOLTIPS.avg_trade_return,
    },
  ]}
  columns={4}
/>

{/* ⚠️ 风险指标 */}
<MetricsCard
  title="风险指标"
  icon="⚠️"
  metrics={[
    {
      title: '最大回撤',
      value: Math.abs(result.results.max_drawdown),
      precision: 2,
      suffix: '%',
      valueStyle: { color: getMetricColor('max_drawdown', result.results.max_drawdown) },
      tooltip: METRIC_TOOLTIPS.max_drawdown,
    },
    {
      title: '回撤持续期',
      value: result.results.max_drawdown_duration || 0,
      precision: 0,
      suffix: '天',
      tooltip: METRIC_TOOLTIPS.max_drawdown_duration,
    },
    {
      title: '波动率',
      value: (result.results.volatility || 0) * 100,
      precision: 2,
      suffix: '%',
      valueStyle: { color: getMetricColor('volatility', (result.results.volatility || 0) * 100) },
      tooltip: METRIC_TOOLTIPS.volatility,
    },
    {
      title: '换手率',
      value: result.results.turnover_rate || 0,
      precision: 2,
      suffix: 'x',
      tooltip: METRIC_TOOLTIPS.turnover_rate,
    },
  ]}
  columns={4}
/>

{/* 🎯 风险调整收益 */}
<MetricsCard
  title="风险调整收益"
  icon="🎯"
  metrics={[
    {
      title: 'Sharpe 比率',
      value: result.results.sharpe_ratio || 0,
      precision: 2,
      valueStyle: { color: getMetricColor('sharpe_ratio', result.results.sharpe_ratio || 0) },
      tooltip: METRIC_TOOLTIPS.sharpe_ratio,
    },
    {
      title: 'Sortino 比率',
      value: result.results.sortino_ratio || 0,
      precision: 2,
      valueStyle: { color: getMetricColor('sortino_ratio', result.results.sortino_ratio || 0) },
      tooltip: METRIC_TOOLTIPS.sortino_ratio,
    },
    {
      title: 'Calmar 比率',
      value: result.results.calmar_ratio || 0,
      precision: 2,
      valueStyle: { color: getMetricColor('calmar_ratio', result.results.calmar_ratio || 0) },
      tooltip: METRIC_TOOLTIPS.calmar_ratio,
    },
    {
      title: '盈亏比',
      value: result.results.profit_factor,
      precision: 2,
      valueStyle: { color: getMetricColor('profit_factor', result.results.profit_factor) },
      tooltip: METRIC_TOOLTIPS.profit_factor,
    },
  ]}
  columns={4}
/>

{/* 📈 交易统计 */}
<MetricsCard
  title="交易统计"
  icon="📈"
  metrics={[
    {
      title: '交易次数',
      value: result.results.total_trades,
      suffix: '次',
      tooltip: METRIC_TOOLTIPS.total_trades,
    },
    {
      title: '胜率',
      value: result.results.win_rate,
      precision: 2,
      suffix: '%',
      tooltip: METRIC_TOOLTIPS.win_rate,
    },
    {
      title: '平均持仓天数',
      value: result.results.avg_holding_period || 0,
      precision: 1,
      suffix: '天',
      tooltip: METRIC_TOOLTIPS.avg_holding_period,
    },
    {
      title: '平均盈利',
      value: result.results.avg_profit,
      precision: 2,
      prefix: '¥',
      tooltip: METRIC_TOOLTIPS.avg_profit,
    },
  ]}
  columns={4}
/>
```

3. **可选：添加元数据显示** (在交易明细后面):

```tsx
{/* 元数据信息 */}
{result.metadata && (
  <Card title="📋 回测元数据" style={{ marginTop: 24 }}>
    <Row gutter={16}>
      <Col xs={24} sm={8}>
        <Statistic
          title="回测ID"
          value={result.metadata.backtest_id}
          valueStyle={{ fontSize: 14 }}
        />
      </Col>
      <Col xs={24} sm={8}>
        <Statistic
          title="引擎版本"
          value={result.metadata.engine_version}
        />
      </Col>
      <Col xs={24} sm={8}>
        <Statistic
          title="执行时间"
          value={result.metadata.execution_time_seconds}
          precision={3}
          suffix="秒"
        />
      </Col>
    </Row>
  </Card>
)}
```

---

## 5. 实施计划

### 5.1 开发任务清单

| 任务ID | 任务描述 | 文件 | 工作量 |
|-------|---------|------|-------|
| T1 | 更新TypeScript类型定义 | `types/index.ts` | 15分钟 |
| T2 | 创建MetricsCard组件 | `components/MetricsCard.tsx` | 30分钟 |
| T3 | 创建指标配置工具 | `utils/metricsConfig.ts` | 20分钟 |
| T4 | 改造BacktestPage | `pages/BacktestPage.tsx` | 45分钟 |
| T5 | 样式调整和优化 | CSS/样式 | 20分钟 |
| T6 | 测试和调试 | - | 30分钟 |
| **总计** | | | **~2.5小时** |

### 5.2 测试计划

#### 5.2.1 功能测试

- [ ] 所有18个指标正确显示
- [ ] Tooltip正确显示
- [ ] 颜色编码正确（正负值、好坏）
- [ ] 元数据正确显示
- [ ] 向后兼容（旧API不报错）

#### 5.2.2 兼容性测试

- [ ] Chrome浏览器
- [ ] Safari浏览器
- [ ] Firefox浏览器
- [ ] 桌面端 (>= 1200px)
- [ ] 平板端 (768px - 1199px)
- [ ] 移动端 (< 768px)

#### 5.2.3 用户体验测试

- [ ] 页面加载速度正常
- [ ] 滚动流畅
- [ ] 视觉层次清晰
- [ ] 无布局错位

---

## 6. 风险与对策

### 6.1 风险1: 后端未返回某些指标

**风险**: 后端可能返回`null`或`undefined`

**对策**: 使用默认值和可选链操作符
```tsx
value: result.results.sharpe_ratio || 0,
value: result.results?.cagr ?? 0,
```

### 6.2 风险2: 页面过长影响体验

**风险**: 4个Card可能导致页面过长

**对策**:
- 方案A: 使用折叠面板 (Collapse)
- 方案B: 使用Tabs标签页
- 方案C: 添加"回到顶部"按钮

### 6.3 风险3: 移动端显示拥挤

**风险**: 移动端显示效果不佳

**对策**:
- 每行显示1-2个指标
- 使用更小的字体
- 隐藏不重要的指标（提供"显示更多"按钮）

---

## 7. 后续优化方向

### 7.1 短期优化（1-2周）

1. **指标对比功能**: 允许对比多次回测的指标
2. **指标导出**: 导出为CSV/Excel
3. **自定义显示**: 用户选择显示哪些指标

### 7.2 中期优化（1-2月）

1. **指标可视化**: 雷达图展示多维度指标
2. **基准对比**: 与沪深300等基准对比
3. **历史回测记录**: 保存和查看历史回测

### 7.3 长期优化（3-6月）

1. **AI解读**: GPT解读指标含义和改进建议
2. **实时更新**: WebSocket实时推送回测进度
3. **多策略对比**: 并排对比多个策略的指标

---

## 8. 参考资料

### 8.1 金融指标定义

- **Sharpe Ratio**: [Investopedia - Sharpe Ratio](https://www.investopedia.com/terms/s/sharperatio.asp)
- **Sortino Ratio**: [Investopedia - Sortino Ratio](https://www.investopedia.com/terms/s/sortinoratio.asp)
- **Calmar Ratio**: [Investopedia - Calmar Ratio](https://www.investopedia.com/terms/c/calmarratio.asp)
- **Max Drawdown**: [Investopedia - Maximum Drawdown](https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp)

### 8.2 设计参考

- Ant Design Statistic: https://ant.design/components/statistic
- Ant Design Card: https://ant.design/components/card
- 量化平台参考: Quantopian, Backtrader, vnpy

---

## 9. 附录

### 9.1 指标计算公式

```python
# 年化收益率 (CAGR)
CAGR = (final_capital / initial_capital) ^ (365 / days) - 1

# Sharpe比率
Sharpe = (年化收益 - 无风险利率) / 年化波动率

# Sortino比率
Sortino = (年化收益 - 无风险利率) / 下行波动率

# Calmar比率
Calmar = 年化收益 / abs(最大回撤)

# 盈亏比
Profit Factor = 总盈利 / abs(总亏损)
```

### 9.2 指标解读标准

| 指标 | 优秀 | 良好 | 一般 | 较差 |
|------|------|------|------|------|
| Sharpe Ratio | >2 | 1-2 | 0-1 | <0 |
| Sortino Ratio | >2 | 1-2 | 0-1 | <0 |
| Calmar Ratio | >3 | 1-3 | 0-1 | <0 |
| Profit Factor | >2 | 1.5-2 | 1-1.5 | <1 |
| Win Rate | >60% | 50-60% | 40-50% | <40% |
| Max Drawdown | <10% | 10-20% | 20-30% | >30% |

---

**文档状态**: ✅ 已完成
**下一步**: 开始实施开发任务
