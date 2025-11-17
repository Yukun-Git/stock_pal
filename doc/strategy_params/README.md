# Strategy Parameters Documentation

This directory contains detailed parameter specifications for all trading strategies in Stock Pal. Each file explains the parameters for a specific strategy, including defaults, ranges, and tuning guidance.

## Available Parameter Guides

- [morning_star_params.md](morning_star_params.md) - Morning Star candlestick pattern parameters
- [ma_cross_params.md](ma_cross_params.md) - Moving Average crossover parameters
- [macd_cross_params.md](macd_cross_params.md) - MACD indicator parameters
- [kdj_cross_params.md](kdj_cross_params.md) - KDJ/Stochastic parameters
- [rsi_reversal_params.md](rsi_reversal_params.md) - RSI reversal parameters
- [boll_breakout_params.md](boll_breakout_params.md) - Bollinger Bands parameters

## What's in Each Parameter Guide

Each parameter document includes:

1. **Parameter Overview**: List of all configurable parameters
2. **Default Values**: Recommended starting values
3. **Parameter Ranges**: Valid ranges for each parameter
4. **Parameter Interactions**: How parameters affect each other
5. **Tuning Guidelines**: How to adjust parameters for different conditions
6. **Common Configurations**: Pre-tested parameter combinations
7. **Examples**: Real backtests with different parameter sets

## Quick Parameter Reference

| Strategy | Key Parameters | Defaults | Tuning Difficulty |
|----------|---------------|----------|-------------------|
| Morning Star | body_ratio, shadow_ratio | 2.0, 1.5 | Medium |
| MA Cross | short_period, long_period | 5, 20 | Easy |
| MACD Cross | fast, slow, signal | 12, 26, 9 | Medium |
| KDJ Cross | k_period, d_period | 9, 3 | Medium |
| RSI Reversal | period, oversold, overbought | 14, 30, 70 | Easy |
| Bollinger Bands | period, std_dev | 20, 2.0 | Easy |

## Parameter Tuning Best Practices

### 1. Start with Defaults
Always begin with default parameters. They're chosen based on market research and common practices.

### 2. One Parameter at a Time
Change one parameter at a time to understand its effect. Don't tune multiple parameters simultaneously.

### 3. Use Multiple Test Cases
Test parameter changes across:
- Different stocks (large-cap, mid-cap, small-cap)
- Different time periods (bull market, bear market, sideways)
- Different date ranges (avoid curve-fitting to one period)

### 4. Watch for Overfitting
If parameters work perfectly on historical data but fail in new tests, you've overfitted. Signs of overfitting:
- Too many trades (capturing noise)
- Too few trades (waiting for perfect conditions)
- Very high win rate (>80%)
- Parameters don't make intuitive sense

### 5. Document Your Findings
When you find good parameter sets, document:
- What you changed
- Why you changed it
- What improved
- What conditions it works best in

## Common Parameter Tuning Scenarios

### Scenario 1: Too Many False Signals

**Problem:** Strategy generates too many trades, many are losers

**Solutions:**
- Increase indicator periods (slower signals)
- Tighten thresholds (stricter entry conditions)
- Add confirmation requirements

**Examples:**
- MA Cross: Increase long period (5/20 → 5/30)
- RSI: Narrow range (30/70 → 25/75)
- MACD: Increase signal period (9 → 12)

### Scenario 2: Missing Opportunities

**Problem:** Strategy is too conservative, misses good trades

**Solutions:**
- Decrease indicator periods (faster signals)
- Loosen thresholds (easier entry conditions)
- Remove overly strict conditions

**Examples:**
- MA Cross: Decrease long period (10/50 → 10/30)
- RSI: Widen range (30/70 → 35/65)
- KDJ: Increase sensitivity

### Scenario 3: Late Entry/Exit

**Problem:** Strategy enters or exits too late

**Solutions:**
- Use shorter indicator periods
- Add leading indicators
- Use faster moving averages

**Examples:**
- MACD: Decrease fast/slow periods (12/26 → 8/17)
- MA Cross: Use shorter periods (5/20 → 3/10)

### Scenario 4: Choppy Markets

**Problem:** Strategy performs poorly in sideways markets

**Solutions:**
- Increase indicator periods (reduce sensitivity)
- Add trend filters
- Use volatility-adjusted parameters

**Examples:**
- Add minimum trend strength requirement
- Use Bollinger Bands to identify ranges
- Adjust RSI thresholds based on volatility

## Parameter Validation

When setting parameters via API, Stock Pal validates:
- Parameters are within allowed ranges
- Required parameters are provided
- Parameter types are correct (int, float)
- Parameter combinations are valid

Invalid parameters will return error messages.

## Advanced: Dynamic Parameters

Currently, Stock Pal uses fixed parameters for each backtest. Future enhancements may include:
- **Adaptive parameters**: Auto-adjust based on market conditions
- **Parameter optimization**: Automated parameter search
- **Market regime detection**: Switch parameter sets based on detected regime

See `/doc/backlog/market_adaptive_configuration.md` for planned features.

## Example: Tuning MA Cross Strategy

### Starting Point
```json
{
  "short_period": 5,
  "long_period": 20
}
```

### Testing Process

**Test 1: Baseline**
- Stock: 600000 (Pudong Development Bank)
- Period: 2023-01-01 to 2023-12-31
- Result: 15% return, 55% win rate

**Test 2: Slower Signals**
```json
{
  "short_period": 10,
  "long_period": 30
}
```
- Result: 12% return, 60% win rate (fewer trades, higher accuracy)

**Test 3: Faster Signals**
```json
{
  "short_period": 3,
  "long_period": 15
}
```
- Result: 18% return, 48% win rate (more trades, lower accuracy but higher total return)

**Conclusion:** Faster signals worked better for this volatile stock in this period. Document findings and test on other stocks.

## Related Documentation

- **Strategy Documentation** (`/doc/strategy/`): Strategy logic and signal rules
- **API Documentation** (`/doc/api/`): How to pass parameters via API
- **Technical Indicators** (`/doc/散户常用技术指标与交易方法论.md`): Indicator theory
- **Backlog** (`/doc/backlog/ai_optimization.md`): Future parameter optimization features

## Tips

1. **Keep a tuning journal**: Document what you try and results
2. **Use realistic commission rates**: Don't optimize for zero-commission scenarios
3. **Test across market cycles**: Include both bull and bear periods
4. **Consider transaction costs**: More trades = more commissions
5. **Think about implementation**: Can you actually execute these signals in practice?

## Need Help?

- See main documentation: `/doc/README.md`
- Check strategy docs: `/doc/strategy/README.md`
- Read API guide: `/doc/api/backtest_engine_v2_usage.md`

---

**Remember:** Parameter tuning is both art and science. Use judgment, not just numbers.
