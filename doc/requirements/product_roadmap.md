# 股票回测系统 - 产品需求分析与路线图

**文档版本**: v1.0
**创建日期**: 2025-11-11
**目标用户**: 股票投资散户

---

## 一、产品定位

### 1.1 核心价值主张
为散户投资者提供**简单易用、专业可靠**的量化回测和智能投资决策工具，降低投资门槛，提高投资成功率。

### 1.2 目标用户画像

**用户A：技术型散户**
- 特征：有一定编程或数据分析能力，关注量化投资
- 痛点：专业量化平台太复杂，学习成本高
- 需求：简单的回测工具、参数优化、策略对比

**用户B：小白散户**（主要目标用户）
- 特征：无技术背景，依赖"感觉"和消息炒股
- 痛点：不知道买什么、何时买卖、如何止损
- 需求：智能选股推荐、买卖信号提醒、简单易懂的操作建议

**用户C：兼职投资者**
- 特征：白天上班，无法盯盘
- 痛点：错过买卖时机、无法及时止损
- 需求：实时信号提醒、自动监控

---

## 二、现有功能评估

### 2.1 已实现功能（v1.0）

✅ **核心回测引擎**
- 支持5种经典策略（MA、MACD、RSI、KDJ、布林带）
- 策略组合模式（AND、OR、VOTE）
- 完整的回测指标（收益率、胜率、最大回撤、盈亏比等）

✅ **可视化展示**
- K线图 + 买卖点标注
- 资产曲线图
- 交易明细表

✅ **当前信号分析**（v1.1新增）
- 分析股票当前是否接近买点/卖点
- 预测需要什么样的价格走势才能触发信号
- 给出操作建议

### 2.2 功能缺失分析

| 功能类别 | 缺失功能 | 用户价值 | 实现难度 | 优先级 |
|---------|---------|---------|---------|--------|
| 回测完善 | 参数优化 | ⭐⭐⭐⭐⭐ | 中 | P0 |
| 风险控制 | 止损止盈 | ⭐⭐⭐⭐⭐ | 低 | P0 |
| 资金管理 | 仓位管理 | ⭐⭐⭐⭐ | 中 | P1 |
| 回测增强 | 多股票组合回测 | ⭐⭐⭐⭐ | 中 | P1 |
| 用户体验 | 回测历史记录 | ⭐⭐⭐ | 低 | P1 |
| 分析能力 | 策略对比 | ⭐⭐⭐ | 低 | P2 |
| 高级分析 | 分时段表现 | ⭐⭐ | 中 | P3 |

---

## 三、核心功能详细设计

### 3.1 参数优化功能 🔥

**功能描述**
- 自动遍历策略参数的多种组合
- 找出历史回测表现最优的参数
- 支持单目标优化（如最大收益率）和多目标优化（收益率+夏普比率）

**用户场景**
> 用户不知道均线金叉策略应该用MA(5,10)还是MA(10,20)，点击"参数优化"按钮，系统自动测试多种组合，推荐最优参数。

**技术方案**
```python
# 参数范围定义
param_ranges = {
    'fast_period': range(5, 30, 5),    # [5, 10, 15, 20, 25]
    'slow_period': range(20, 100, 10)  # [20, 30, ..., 90]
}

# 优化算法
1. 网格搜索（Grid Search）：遍历所有组合
2. 随机搜索（Random Search）：随机采样N个组合
3. 贝叶斯优化（进阶）：智能搜索
```

**UI设计**
- 参数优化按钮（在回测配置页面）
- 优化进度条
- 结果展示：
  - 最优参数组合
  - 参数热力图（不同参数组合的收益率分布）
  - Top 10 参数组合对比

**实现难度**: 中等
**开发时间**: 3-5天
**优先级**: P0（高优先级）

---

### 3.2 止损止盈设置 🔥

**功能描述**
- 固定比例止损：跌幅超过X%自动卖出
- 固定比例止盈：涨幅超过Y%自动卖出
- 移动止损（跟踪止损）：价格回撤超过Z%卖出
- 止损止盈优先级高于策略信号

**用户场景**
> 用户使用MA策略回测，发现某次交易亏损达到-20%才卖出。设置8%止损后，最大单笔亏损控制在-8%以内，整体回撤显著降低。

**技术方案**
```python
class RiskManagement:
    def __init__(self, stop_loss_pct, take_profit_pct, trailing_stop_pct):
        self.stop_loss = stop_loss_pct
        self.take_profit = take_profit_pct
        self.trailing_stop = trailing_stop_pct

    def should_exit(self, entry_price, current_price, highest_price):
        # 固定止损
        if (current_price - entry_price) / entry_price < -self.stop_loss:
            return True, "止损"

        # 固定止盈
        if (current_price - entry_price) / entry_price > self.take_profit:
            return True, "止盈"

        # 移动止损
        if (current_price - highest_price) / highest_price < -self.trailing_stop:
            return True, "跟踪止损"

        return False, None
```

**UI设计**
- 回测配置中添加风控选项：
  - 止损比例（默认0，不启用）
  - 止盈比例（默认0，不启用）
  - 移动止损（默认0，不启用）
- 回测结果中标注止损/止盈卖出点（用不同颜色标识）
- 统计：
  - 止损次数/止盈次数
  - 止损避免的最大亏损

**实现难度**: 简单
**开发时间**: 1-2天
**优先级**: P0（高优先级）

---

### 3.3 仓位管理 🔥

**功能描述**
- 固定比例建仓：每次买入使用总资金的X%
- 固定金额建仓：每次买入固定金额
- 金字塔加仓：盈利后按比例加仓
- 分批建仓：分N次买入
- 凯利公式（进阶）：根据胜率和盈亏比动态调整仓位

**用户场景**
> 用户有10万资金，不想all-in。设置每次使用30%仓位，即每次最多买入3万元，剩余资金保留现金或投资其他股票。

**技术方案**
```python
class PositionManager:
    def __init__(self, mode, ratio=None, amount=None):
        self.mode = mode  # 'fixed_ratio', 'fixed_amount', 'pyramid'
        self.ratio = ratio
        self.amount = amount

    def calculate_shares_to_buy(self, available_capital, current_price):
        if self.mode == 'fixed_ratio':
            buy_amount = available_capital * self.ratio
        elif self.mode == 'fixed_amount':
            buy_amount = min(self.amount, available_capital)

        shares = int(buy_amount / current_price / 100) * 100  # 手为单位
        return shares
```

**UI设计**
- 仓位管理设置：
  - 模式选择：固定比例/固定金额/金字塔
  - 参数输入：比例或金额
- 回测结果中显示：
  - 每次交易的仓位占比
  - 资金利用率
  - 最大持仓金额

**实现难度**: 中等
**开发时间**: 2-3天
**优先级**: P1

---

### 3.4 多股票组合回测

**功能描述**
- 同时回测多只股票（如沪深300成分股）
- 轮动策略：资金在多只股票间切换
- 组合表现：整体收益、相关性分析
- 行业分散度分析

**用户场景**
> 用户想知道同一策略在不同股票上的表现差异，或者构建一个10只股票的组合，看整体风险收益。

**技术方案**
```python
def backtest_portfolio(symbols, strategy, capital):
    # 1. 为每只股票分配资金
    capital_per_stock = capital / len(symbols)

    # 2. 分别回测
    results = {}
    for symbol in symbols:
        results[symbol] = backtest_single(symbol, strategy, capital_per_stock)

    # 3. 合并结果
    portfolio_equity = combine_equity_curves(results)

    # 4. 计算组合指标
    return calculate_portfolio_metrics(portfolio_equity)
```

**UI设计**
- 股票选择：支持多选或导入自选股
- 组合模式：
  - 平均分配：每只股票相同资金
  - 自定义权重：手动设置比例
  - 轮动模式：同时只持有N只，其他观望
- 结果展示：
  - 组合整体收益曲线
  - 各股票表现对比
  - 相关性矩阵热力图

**实现难度**: 中等
**开发时间**: 4-5天
**优先级**: P1

---

### 3.5 回测历史记录

**功能描述**
- 自动保存每次回测结果
- 历史记录列表（时间、股票、策略、收益率）
- 快速查看历史回测详情
- 对比多次回测结果

**用户场景**
> 用户昨天对茅台回测了MA策略，今天想再看看，不用重新运行，直接从历史记录中打开。

**技术方案**
```python
# 数据库表设计
class BacktestRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)  # 如果有用户系统
    symbol = db.Column(db.String(20))
    strategy_ids = db.Column(db.JSON)  # ['ma_cross', 'macd_cross']
    parameters = db.Column(db.JSON)
    date_range = db.Column(db.JSON)
    results = db.Column(db.JSON)  # 完整结果
    created_at = db.Column(db.DateTime)
```

**UI设计**
- 新增"历史记录"页面/标签
- 列表展示：
  - 时间、股票名称、策略、收益率、胜率
  - 操作：查看详情、删除、对比
- 详情页：完整的回测结果（与当前回测结果页相同）

**实现难度**: 简单
**开发时间**: 2天
**优先级**: P1

---

## 四、新增大功能方向

### 4.1 智能选股助手 🌟

**功能描述**
- 全市场扫描：基于用户策略，扫描沪深A股/港股
- 信号强度排序：按接近买入信号的程度排序
- 行业分布：展示哪些行业当前机会多
- 自选股监控：用户自定义关注列表

**用户场景**
> 用户不知道买什么股票。打开"选股助手"，系统自动推荐10只当前接近MA金叉的股票，用户点击即可查看详情和回测。

**技术方案**
```python
def scan_market(strategy, signal_type='buy'):
    # 1. 获取股票列表（沪深300或全市场）
    symbols = get_stock_list('hs300')

    # 2. 并发获取数据和计算指标
    results = []
    for symbol in symbols:
        df = get_stock_data(symbol)
        df = calculate_indicators(df)
        df = apply_strategy(strategy, df)

        # 3. 分析信号强度
        signal_strength = analyze_signal_proximity(df, signal_type)

        if signal_strength > 0:
            results.append({
                'symbol': symbol,
                'strength': signal_strength,
                'current_state': get_current_state(df)
            })

    # 4. 按信号强度排序
    return sorted(results, key=lambda x: x['strength'], reverse=True)
```

**UI设计**
- 新增"选股助手"页面
- 配置区：
  - 选择策略
  - 选择股票池（沪深300/自选股/全市场）
  - 信号类型（买入/卖出）
- 结果展示：
  - 推荐股票列表（带信号强度指示器）
  - 点击查看详情（当前状态、技术指标、快速回测）
  - 加入自选股按钮

**实现难度**: 中高
**开发时间**: 5-7天
**优先级**: P0（杀手级功能）

---

### 4.2 实时信号提醒 🌟

**功能描述**
- 用户设置监控：股票 + 策略
- 实时数据更新（每分钟/每5分钟）
- 信号触发时：
  - 网站内消息提醒
  - 邮件提醒
  - 微信/Telegram推送（可选）

**用户场景**
> 用户监控茅台的MA金叉策略，当金叉出现时，收到邮件："茅台触发买入信号，当前价格1850元，建议关注"。

**技术方案**
```python
# 定时任务（Celery + Redis）
@celery.task
def monitor_signals():
    # 1. 获取所有用户的监控配置
    monitors = get_all_monitors()

    for monitor in monitors:
        # 2. 获取最新数据
        df = get_realtime_data(monitor.symbol)
        df = calculate_indicators(df)
        df = apply_strategy(monitor.strategy, df)

        # 3. 检查信号
        latest_signal = df.iloc[-1]['signal']

        if latest_signal != 0:
            # 4. 发送提醒
            send_notification(
                user=monitor.user,
                symbol=monitor.symbol,
                signal='买入' if latest_signal == 1 else '卖出',
                price=df.iloc[-1]['close']
            )
```

**UI设计**
- 新增"信号监控"页面
- 添加监控：
  - 选择股票
  - 选择策略
  - 选择提醒方式
- 监控列表：
  - 股票名称、策略、状态、最后检查时间
  - 操作：暂停/删除
- 通知中心：
  - 历史提醒记录

**实现难度**: 中高
**开发时间**: 7-10天
**优先级**: P0

---

### 4.3 投资组合跟踪器 🌟

**功能描述**
- 用户输入实际持仓（股票、数量、成本价）
- 实时显示总资产、盈亏
- 结合策略给出持仓建议（哪些应该卖出）
- 风险分析（集中度、行业分布）

**用户场景**
> 用户持有5只股票，在"组合跟踪"中输入持仓信息，系统显示当前盈亏-3.2%，并提示："比亚迪触发MACD死叉，建议考虑减仓"。

**技术方案**
```python
class Portfolio:
    def __init__(self, holdings):
        self.holdings = holdings  # [{symbol, shares, cost}]

    def calculate_metrics(self):
        total_value = 0
        total_cost = 0

        for holding in self.holdings:
            current_price = get_realtime_price(holding['symbol'])
            value = current_price * holding['shares']
            cost = holding['cost'] * holding['shares']

            total_value += value
            total_cost += cost

        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'profit': total_value - total_cost,
            'profit_pct': (total_value - total_cost) / total_cost * 100
        }

    def get_signals(self, strategy):
        signals = []
        for holding in self.holdings:
            signal = check_strategy_signal(holding['symbol'], strategy)
            if signal != 0:
                signals.append({
                    'symbol': holding['symbol'],
                    'action': '买入' if signal == 1 else '卖出',
                    'reason': get_signal_reason(holding['symbol'], strategy)
                })
        return signals
```

**UI设计**
- 新增"我的组合"页面
- 持仓管理：
  - 添加持仓（股票、数量、成本价）
  - 编辑/删除持仓
- 组合总览：
  - 总资产、总成本、总盈亏（大卡片展示）
  - 饼图：行业分布、个股占比
- 持仓明细表：
  - 每只股票的实时价格、盈亏、涨跌幅
  - 策略信号提示（红色=卖出建议，绿色=买入建议）
- 操作建议：
  - 基于策略的买卖建议列表

**实现难度**: 中等
**开发时间**: 5-7天
**优先级**: P1

---

### 4.4 AI投资助手（ChatBot）

**功能描述**
- 自然语言交互："茅台现在能买吗？"
- AI分析：
  - 当前技术指标状态
  - 策略回测历史表现
  - 风险提示
  - 给出建议
- 支持追问："如果跌到1800可以买吗？"

**用户场景**
> 用户问："比亚迪现在怎么样？"
> AI回答："比亚迪当前价格220元，RSI=65处于中性偏高区域，MACD处于金叉状态但柱状图缩短。根据MA(5,20)策略的历史回测，当前位置买入的平均收益率为+5.2%，胜率62%。建议：可以小仓位试探，设置8%止损。"

**技术方案**
```python
def ai_assistant(user_question, context):
    # 1. 解析用户意图（使用LLM）
    intent = parse_intent(user_question)  # "查询股票状态"

    # 2. 提取关键信息
    symbol = extract_symbol(user_question)  # "比亚迪" -> "002594"

    # 3. 获取数据和分析
    stock_data = get_stock_data(symbol)
    indicators = calculate_indicators(stock_data)
    backtest_stats = get_backtest_history(symbol)

    # 4. 构造Prompt
    prompt = f"""
    用户问题：{user_question}

    股票信息：
    - 当前价格：{stock_data['close']}
    - RSI(14): {indicators['rsi14']}
    - MACD: DIF={indicators['dif']}, DEA={indicators['dea']}

    历史回测表现：
    - 平均收益率：{backtest_stats['avg_return']}
    - 胜率：{backtest_stats['win_rate']}

    请基于以上信息，用通俗易懂的语言回答用户的问题，并给出投资建议。
    """

    # 5. 调用LLM
    response = call_llm_api(prompt)

    return response
```

**UI设计**
- 新增"AI助手"页面或悬浮按钮
- 聊天界面（类似ChatGPT）
- 快捷提问模板：
  - "分析[股票名]"
  - "[股票名]现在能买吗？"
  - "推荐一些科技股"

**实现难度**: 中高（需要LLM API）
**开发时间**: 5-7天
**优先级**: P2（差异化功能）

---

### 4.5 可视化策略创建器

**功能描述**
- 拖拽式策略编辑器
- 无需编程，用图形化方式创建策略
- 实时预览和回测

**用户场景**
> 用户想创建策略："RSI<30且MACD金叉时买入"，通过拖拽条件块组合，无需写代码。

**技术方案**
- 前端：使用类似Scratch的可视化编程库（如Blockly）
- 后端：将可视化配置转换为策略代码

**实现难度**: 高
**开发时间**: 10-14天
**优先级**: P3（高级功能）

---

## 五、产品路线图

### 阶段1：回测功能完善（1-2周）

**目标**：让回测更加专业和实用

- [ ] 止损止盈设置
- [ ] 参数优化功能
- [ ] 回测历史记录
- [ ] 策略对比功能

**里程碑**：回测功能达到专业量化平台水平

---

### 阶段2：智能化升级（3-4周）

**目标**：从工具变成助手

- [ ] 智能选股助手
- [ ] 实时信号提醒
- [ ] 仓位管理
- [ ] 多股票组合回测

**里程碑**：用户可以依赖系统进行日常投资决策

---

### 阶段3：实盘管理（5-8周）

**目标**：连接回测和实盘

- [ ] 投资组合跟踪器
- [ ] 交易日志
- [ ] 绩效归因分析
- [ ] 风险监控面板

**里程碑**：覆盖投资全流程（选股→回测→实盘→跟踪）

---

### 阶段4：AI与社区（9-12周）

**目标**：差异化竞争力

- [ ] AI投资助手
- [ ] 策略市场（用户分享策略）
- [ ] 社区讨论
- [ ] 策略可视化创建器

**里程碑**：形成用户生态

---

## 六、商业化思路

### 6.1 免费版（引流）
- 基础回测功能
- 5个预设策略
- 每日3次回测限制
- 广告支持

### 6.2 标准版（¥99/月或¥999/年）
- 无限次回测
- 参数优化
- 历史记录
- 10只股票监控
- 邮件提醒

### 6.3 专业版（¥299/月或¥2999/年）
- 所有功能
- 全市场选股扫描
- 无限股票监控
- 微信/短信提醒
- AI助手
- 组合管理

### 6.4 其他收入
- 策略市场（用户售卖策略，平台抽成）
- 付费课程（量化投资教学）
- 导流券商（开户返佣）

---

## 七、竞品分析

### 7.1 主要竞品

| 产品 | 定位 | 优势 | 劣势 | 我们的差异化 |
|-----|------|------|------|------------|
| 聚宽/米筐 | 专业量化平台 | 功能强大、数据全 | 学习成本高、需要编程 | 更简单、面向散户 |
| 同花顺/东方财富 | 综合金融平台 | 用户多、数据全 | 回测功能弱、无智能推荐 | 专注量化回测和AI推荐 |
| 雪球 | 投资社区 | 社区活跃、消息快 | 无量化工具 | 量化+社区结合 |
| TradingView | 技术分析工具 | 图表强大、全球市场 | 回测复杂、偏向外盘 | 专注A股、更易用 |

### 7.2 差异化策略

1. **降低门槛**：小白也能用的量化工具
2. **智能推荐**：从"工具"到"助手"
3. **实时提醒**：解决上班族痛点
4. **AI加持**：自然语言交互，降低学习成本
5. **社区生态**：策略分享，形成网络效应

---

## 八、技术架构建议

### 8.1 当前架构（v1.0）
- 后端：Flask + Python
- 前端：React + TypeScript + Ant Design
- 数据：AkShare（免费）
- 部署：Docker

### 8.2 未来优化方向

**数据层**
- 引入更高质量数据源（考虑付费API）
- 数据缓存优化（Redis）
- 历史数据存储（时序数据库InfluxDB）

**计算层**
- 异步任务队列（Celery + RabbitMQ）
- 并行计算（多进程/GPU加速）
- 分布式计算（大规模回测）

**前端**
- 更丰富的图表（TradingView库）
- 移动端适配（响应式/小程序）

**AI层**
- LLM接入（Claude/GPT-4）
- 本地模型（成本优化）

---

## 九、成功指标（KPI）

### 9.1 产品指标
- DAU（日活用户）：目标1000+
- 留存率：次日留存>40%，7日留存>20%
- 回测次数：每用户每周平均3次+
- 付费转化率：5-10%

### 9.2 功能指标
- 参数优化使用率：>30%
- 选股助手使用率：>50%
- 信号提醒准确率：>80%
- AI助手满意度：>4.0/5.0

---

## 十、风险与挑战

### 10.1 合规风险
- 不能承诺收益（免责声明）
- 不能推荐具体买卖（教育定位）
- 数据合规（数据来源合法性）

### 10.2 技术挑战
- 实时数据获取成本
- 大规模计算性能
- 数据准确性

### 10.3 运营挑战
- 用户教育（量化概念普及）
- 用户留存（避免"用完就走"）
- 口碑传播（如何引发分享）

---

## 十一、下一步行动

### 优先级P0（立即开始）
1. [ ] 止损止盈功能（1-2天）
2. [ ] 参数优化功能（3-5天）
3. [ ] 智能选股助手（5-7天）

### 快速验证（MVP）
- 先完成核心功能的简化版
- 找10-20个目标用户内测
- 收集反馈，快速迭代

### 长期规划
- 保持每2周发布一个新功能
- 3个月内完成阶段2目标
- 6个月内达到1000用户

---

**文档维护**：本文档应根据用户反馈和市场变化持续更新。
