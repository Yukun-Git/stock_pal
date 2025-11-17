# 基准对比功能开发进度

**功能**: P0 - 基准对比API集成
**设计文档**: `doc/design/backtest_post_mvp_enhancements.md`
**开始时间**: 2025-11-16
**状态**: ✅ 后端完成 | ⏸️ 前端待定

---

## 开发进度总览

### 后端开发 (100% 完成)

#### ✅ 1. BenchmarkService 实现
**完成时间**: 2025-11-16
**文件**: `backend/app/services/benchmark_service.py`

**功能**:
- [x] 支持4种基准指数（沪深300、中证500、创业板指、科创50）
- [x] 使用AkShare `stock_zh_index_daily_em()` 获取数据
- [x] 实现内存缓存机制
- [x] 提供基准列表查询API
- [x] 计算基准收益率和权益曲线
- [x] 日期对齐功能

**关键实现**:
```python
# 基准指数映射
BENCHMARK_MAP = {
    'CSI300': {'em_symbol': 'sh000300', 'name': '沪深300'},
    'CSI500': {'em_symbol': 'sh000905', 'name': '中证500'},
    'GEM': {'em_symbol': 'sz399006', 'name': '创业板指'},
    'STAR50': {'em_symbol': 'sh000688', 'name': '科创50'}
}

# 主要方法
- get_benchmark_list()
- get_benchmark_data(benchmark_id, start_date, end_date)
- calculate_benchmark_returns(benchmark_data)
- calculate_benchmark_equity(benchmark_data, initial_capital)
```

#### ✅ 2. BacktestOrchestrator 增强
**完成时间**: 2025-11-16
**文件**: `backend/app/backtest/orchestrator.py`

**功能**:
- [x] `run()` 方法支持可选的 `benchmark_id` 参数
- [x] 自动获取基准数据并对齐日期
- [x] 计算基准收益率序列
- [x] 将基准数据传递给指标计算器
- [x] 基准数据附加到回测结果

**关键代码**:
```python
def run(self, market_data, signals, stock_info=None, benchmark_id=None):
    # 获取基准数据
    if benchmark_id:
        benchmark_df = BenchmarkService.get_benchmark_data(...)
        benchmark_returns = BenchmarkService.calculate_benchmark_returns(...)
        benchmark_equity_df = BenchmarkService.calculate_benchmark_equity(...)

    # 计算指标（传入基准收益率）
    metrics = MetricsCalculator.calculate_all_metrics(
        equity_curve, trades, benchmark_returns=benchmark_returns
    )
```

#### ✅ 3. API 端点增强
**完成时间**: 2025-11-16
**文件**: `backend/app/api/v1/backtest.py`, `backend/app/api/v1/__init__.py`

**功能**:
- [x] POST `/api/v1/backtest` 支持 `benchmark` 参数
- [x] 返回基准权益曲线数据
- [x] 返回基准指标（总收益、CAGR、Sharpe、最大回撤、波动率）
- [x] 返回相对基准指标（Alpha、Beta、Information Ratio、Tracking Error）
- [x] GET `/api/v1/benchmarks` 返回支持的基准列表

**API 示例**:
```json
// 请求
{
  "symbol": "000001",
  "strategy_id": "ma_cross",
  "start_date": "20230101",
  "end_date": "20231231",
  "benchmark": "CSI300"  // 新增参数
}

// 响应（新增字段）
{
  "data": {
    "results": {
      "alpha": -0.2488,           // 新增
      "beta": 0.28,               // 新增
      "information_ratio": -0.96, // 新增
      "tracking_error": 0.1452    // 新增
    },
    "benchmark": {                // 新增整个对象
      "id": "CSI300",
      "name": "沪深300",
      "equity_curve": [...],
      "metrics": {
        "total_return": -0.1175,
        "cagr": -0.1220,
        "sharpe_ratio": -1.12,
        "max_drawdown": -0.2151,
        "volatility": 0.1523
      }
    }
  }
}
```

#### ✅ 4. 指标计算增强
**文件**: `backend/app/backtest/metrics.py` (已有)

**功能**:
- [x] Alpha 计算
- [x] Beta 计算
- [x] Information Ratio 计算
- [x] Tracking Error 计算
- [x] `calculate_all_metrics()` 支持传入 `benchmark_returns`

**说明**: 这些指标计算方法在之前的回测引擎升级中已经实现，本次只需集成使用。

---

## 测试验证

### ✅ 功能测试
**测试时间**: 2025-11-16

**测试用例**:
- 股票: 000001 (平安银行)
- 策略: ma_cross (短周期5, 长周期20)
- 日期范围: 2023-01-01 至 2023-12-31
- 基准: CSI300 (沪深300)

**测试结果**:
```
策略指标:
- 总收益率: -22.62%
- 年化收益率(CAGR): -23.44%
- 夏普比率: -2.55
- 最大回撤: -22.82%
- 胜率: 0.00%

基准指标 (沪深300):
- 总收益率: -11.75%
- 年化收益率(CAGR): -12.20%
- 夏普比率: -1.12
- 最大回撤: -21.51%

相对基准指标:
- Alpha (超额收益): -24.88%
- Beta (系统风险): 0.28
- 信息比率: -0.96
- 跟踪误差: 14.52%
```

**结论**: ✅ 所有功能正常工作

### ✅ API 测试
- [x] GET `/api/v1/benchmarks` - 返回4种基准列表
- [x] POST `/api/v1/backtest` (无benchmark参数) - 正常回测
- [x] POST `/api/v1/backtest` (有benchmark参数) - 返回基准对比数据

---

## 验收标准完成情况

根据 `doc/design/backtest_post_mvp_enhancements.md` 第7.2节：

### P0 基准对比 - 后端部分
- [x] ✅ API返回Alpha/Beta/IR/TE
- [x] ✅ API返回基准权益曲线
- [ ] ⏸️ 前端显示基准对比指标
- [ ] ⏸️ 前端图表叠加基准曲线
- [x] ✅ 支持4种基准指数

**后端完成度**: 100%
**前端完成度**: 0% (待定)

---

## 技术细节

### 数据获取
使用 AkShare 的 `stock_zh_index_daily_em()` 函数获取指数数据：
- 沪深300: `sh000300`
- 中证500: `sh000905`
- 创业板指: `sz399006`
- 科创50: `sh000688`

### 缓存策略
使用简单的内存字典缓存：
```python
cache_key = f"{benchmark_id}_{start_date}_{end_date}"
```
**说明**: 生产环境建议使用 Redis 等持久化缓存。

### 日期对齐
策略和基准的交易日可能不完全一致，通过 pandas 的 `align()` 方法取交集。

### 指标计算
所有基准对比指标基于日收益率计算：
- Alpha: 策略超额收益（相对CAPM模型）
- Beta: 策略对基准的敏感度（协方差/方差）
- Information Ratio: 超额收益/跟踪误差
- Tracking Error: 收益率差的标准差（年化）

---

## 遗留问题

### 已知限制
1. **缓存策略**: 当前使用内存缓存，重启服务后失效
   - **建议**: 后续迁移到 Redis

2. **基准数据延迟**: AkShare 数据可能有1-2天延迟
   - **影响**: 最新交易日可能无基准数据
   - **对策**: 已实现异常处理，基准获取失败时不影响回测

3. **日期对齐**: 取交集可能导致部分交易日无基准数据
   - **影响**: 基准对比指标可能略有偏差
   - **现状**: 可接受

### 未实现功能（可选）
1. **前端展示**: 基准对比卡片和图表叠加
2. **更多基准**: 科创创业50、深证成指等
3. **自定义基准**: 支持用户自定义基准组合

---

## 下一步计划

### Option 1: 前端开发（完成 P0 基准对比的前端部分）
**预计工时**: 2-3小时

**任务**:
1. 在 BacktestPage 添加基准选择下拉框
2. 新增 BenchmarkComparisonCard 组件显示 Alpha/Beta/IR/TE
3. 在 EquityCurveChart 中叠加基准曲线（双Y轴）
4. 更新类型定义和API调用

### Option 2: 转向 P1 数据库持久化
**优先级**: P1（产品功能）

**任务**:
- 回测结果保存到数据库
- 历史回测查询API
- 回测对比功能
- 导出功能

---

## 相关文件清单

### 新增文件
- `backend/app/services/benchmark_service.py` - 基准服务

### 修改文件
- `backend/app/backtest/orchestrator.py` - 增强 run() 方法
- `backend/app/api/v1/backtest.py` - 增强 BacktestResource, 新增 BenchmarkListResource
- `backend/app/api/v1/__init__.py` - 注册新路由

### 测试文件
- `/tmp/test_benchmark_backtest.py` - 功能测试脚本

---

**最后更新**: 2025-11-16
**文档状态**: ✅ 已完成
**开发者**: Claude Code
