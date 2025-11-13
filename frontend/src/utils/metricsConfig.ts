/**
 * 回测指标配置工具
 *
 * 提供指标的 Tooltip 说明和颜色编码逻辑
 */

/**
 * 指标 Tooltip 说明文案
 */
export const METRIC_TOOLTIPS: Record<string, string> = {
  // ===== 收益指标 =====
  total_return: "整个回测期间的总收益率",
  cagr: "年化复合增长率（CAGR），衡量策略的长期收益能力。考虑了复利效应，适合评估长期投资表现",
  final_capital: "回测结束时的总资金",
  avg_trade_return: "每次交易的平均收益率，正值表示平均盈利，负值表示平均亏损",

  // ===== 风险指标 =====
  max_drawdown: "从最高点到最低点的最大亏损幅度。<10%低风险，10-20%中风险，>20%高风险",
  max_drawdown_duration: "从最高点到恢复所需的最长时间（交易日）。持续时间越短，恢复能力越强",
  volatility: "收益波动率（年化），衡量策略的稳定性。越低表示收益越稳定",
  turnover_rate: "年化换手率，衡量交易频率。值越大表示交易越频繁",

  // ===== 风险调整收益 =====
  sharpe_ratio: "夏普比率 = (年化收益 - 无风险利率) / 波动率。衡量每单位风险的超额收益。>1优秀，>2非常好",
  sortino_ratio: "索提诺比率，只考虑下行风险的收益指标。相比Sharpe更关注负面波动，越高越好",
  calmar_ratio: "卡玛比率 = 年化收益 / 最大回撤。衡量单位回撤的收益能力，越高越好",
  profit_factor: "盈亏比 = 总盈利 / 总亏损。>1表示盈利，>2优秀，>3非常好",

  // ===== 交易统计 =====
  total_trades: "回测期间的总交易次数（买入和卖出各算一次）",
  win_rate: "盈利交易占总交易的比例。>60%优秀，50-60%良好，<40%需要改进",
  avg_holding_period: "平均每次交易持有的天数。可以判断策略是短线、中线还是长线",
  avg_profit: "盈利交易的平均金额",
  avg_loss: "亏损交易的平均金额（取绝对值显示）",

  // ===== 元数据 =====
  backtest_id: "回测的唯一标识符，用于追踪和复现",
  engine_version: "回测引擎的版本号",
  execution_time: "回测执行耗时（秒）",
};

/**
 * 根据指标名称和值返回对应的颜色
 *
 * @param metricName - 指标名称
 * @param value - 指标值
 * @returns CSS 颜色值
 */
export function getMetricColor(metricName: string, value: number): string {
  // 处理 NaN 或 undefined
  if (value === undefined || value === null || isNaN(value)) {
    return '#262626'; // 默认黑色
  }

  // ===== 收益类指标：正红负绿 =====
  if (['total_return', 'cagr', 'avg_trade_return', 'avg_profit'].includes(metricName)) {
    return value >= 0 ? '#ff4d4f' : '#52c41a';
  }

  // ===== 比率指标：根据阈值判断好坏 =====
  if (['sharpe_ratio', 'sortino_ratio', 'calmar_ratio'].includes(metricName)) {
    if (value >= 2) return '#52c41a';      // 绿色：优秀
    if (value >= 1) return '#faad14';      // 橙色：良好
    if (value >= 0) return '#262626';      // 黑色：一般
    return '#ff4d4f';                       // 红色：较差
  }

  // ===== 盈亏比：特殊处理 =====
  if (metricName === 'profit_factor') {
    if (value >= 2) return '#52c41a';      // 绿色：优秀
    if (value >= 1) return '#faad14';      // 橙色：盈利
    return '#ff4d4f';                       // 红色：亏损
  }

  // ===== 胜率：百分比判断 =====
  if (metricName === 'win_rate') {
    if (value >= 60) return '#52c41a';     // 绿色：优秀
    if (value >= 50) return '#faad14';     // 橙色：良好
    if (value >= 40) return '#262626';     // 黑色：一般
    return '#ff4d4f';                       // 红色：较差
  }

  // ===== 风险指标：值越大越危险（使用绝对值） =====
  if (['max_drawdown', 'volatility'].includes(metricName)) {
    const absValue = Math.abs(value);
    if (metricName === 'max_drawdown') {
      // 最大回撤（百分比形式，如15表示15%）
      if (absValue > 30) return '#ff4d4f';  // 红色：高风险
      if (absValue > 20) return '#faad14';  // 橙色：中风险
      if (absValue > 10) return '#52c41a';  // 绿色：低风险
      return '#52c41a';                      // 绿色：很低风险
    } else if (metricName === 'volatility') {
      // 波动率（百分比形式，如20表示20%）
      if (absValue > 30) return '#ff4d4f';  // 红色：高波动
      if (absValue > 20) return '#faad14';  // 橙色：中波动
      if (absValue > 10) return '#52c41a';  // 绿色：低波动
      return '#52c41a';                      // 绿色：很低波动
    }
  }

  // ===== 默认：中性色（黑色） =====
  return '#262626';
}

/**
 * 格式化指标值为显示文本
 *
 * @param value - 指标值
 * @returns 格式化后的字符串
 */
export function formatMetricValue(_metricName: string, value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) {
    return '-';
  }

  // 直接返回（所有百分比指标在传入前已经转换）
  return value.toString();
}

/**
 * 获取指标的推荐精度（小数位数）
 *
 * @param metricName - 指标名称
 * @returns 小数位数
 */
export function getMetricPrecision(metricName: string): number {
  // 整数指标
  if (['total_trades', 'winning_trades', 'losing_trades', 'max_drawdown_duration'].includes(metricName)) {
    return 0;
  }

  // 1位小数
  if (['avg_holding_period'].includes(metricName)) {
    return 1;
  }

  // 默认2位小数
  return 2;
}

/**
 * 指标分组配置
 */
export const METRIC_GROUPS = {
  returns: {
    title: '收益指标',
    icon: '📊',
    metrics: ['total_return', 'cagr', 'final_capital', 'avg_trade_return']
  },
  risk: {
    title: '风险指标',
    icon: '⚠️',
    metrics: ['max_drawdown', 'max_drawdown_duration', 'volatility', 'turnover_rate']
  },
  riskAdjusted: {
    title: '风险调整收益',
    icon: '🎯',
    metrics: ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'profit_factor']
  },
  trading: {
    title: '交易统计',
    icon: '📈',
    metrics: ['total_trades', 'win_rate', 'avg_holding_period', 'avg_profit']
  }
} as const;
