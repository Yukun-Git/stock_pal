# Trading Strategy Documentation

This directory contains documentation for all trading strategies implemented in Stock Pal. Each strategy has its own documentation file explaining the logic, signals, and use cases.

## Available Strategies

Stock Pal currently implements 6 trading strategies based on popular technical indicators:

1. **[Morning Star](morning_star.md)** - Candlestick pattern reversal strategy
2. **[MA Cross](ma_cross.md)** - Moving Average crossover strategy
3. **[MACD Cross](macd_cross.md)** - MACD indicator crossover strategy
4. **[KDJ Cross](kdj_cross.md)** - KDJ (Stochastic) indicator strategy
5. **[RSI Reversal](rsi_reversal.md)** - RSI overbought/oversold reversal strategy
6. **[Bollinger Breakout](boll_breakout.md)** - Bollinger Bands breakout strategy

## Strategy Categories

### Trend-Following Strategies
Strategies that identify and follow market trends:
- **MA Cross**: Uses moving average crossovers to identify trend changes
- **MACD Cross**: Uses MACD crossovers to capture momentum shifts

### Mean-Reversion Strategies
Strategies that bet on price returning to average:
- **RSI Reversal**: Identifies overbought/oversold conditions
- **Bollinger Breakout**: Trades breakouts from volatility bands

### Momentum Strategies
Strategies based on momentum indicators:
- **KDJ Cross**: Uses stochastic oscillator for momentum signals
- **MACD Cross**: Also captures momentum (dual purpose)

### Pattern Recognition
Strategies based on candlestick patterns:
- **Morning Star**: Identifies bullish reversal patterns

## How to Use Strategy Documentation

Each strategy document includes:

### 1. Strategy Overview
- Brief description
- Market conditions where it works best
- Key characteristics

### 2. Technical Indicators Used
- Which indicators are required
- How they're calculated
- Parameter defaults

### 3. Signal Generation Rules

**Buy Signals:**
- Specific conditions that trigger buy
- Example scenarios

**Sell Signals:**
- Specific conditions that trigger sell
- Example scenarios

### 4. Parameters

Each strategy has configurable parameters. For detailed parameter documentation, see the corresponding file in `/doc/strategy_params/`:

- [morning_star_params.md](../strategy_params/morning_star_params.md)
- [ma_cross_params.md](../strategy_params/ma_cross_params.md)
- [macd_cross_params.md](../strategy_params/macd_cross_params.md)
- [kdj_cross_params.md](../strategy_params/kdj_cross_params.md)
- [rsi_reversal_params.md](../strategy_params/rsi_reversal_params.md)
- [boll_breakout_params.md](../strategy_params/boll_breakout_params.md)

### 5. Strengths & Weaknesses
- When the strategy performs well
- Known limitations
- Market conditions to avoid

### 6. Example Usage
- Sample backtest scenarios
- Parameter tuning tips
- Combination with other strategies

## Understanding Strategy Parameters

Most strategies have parameters that can be tuned:

**Common parameter types:**
- **Period lengths**: How many days to look back (e.g., MA period)
- **Thresholds**: Trigger levels (e.g., RSI overbought at 70)
- **Smoothing factors**: For indicator calculation (e.g., EMA smoothing)

**How to tune parameters:**
1. Start with default values
2. Run backtests on different stocks and time periods
3. Adjust parameters based on results
4. Avoid overfitting to historical data
5. Test on out-of-sample data

See `/doc/strategy_params/` for detailed parameter guides.

## Strategy Selection Guide

### For Trending Markets
Choose trend-following strategies:
- **MA Cross** (simple, reliable in strong trends)
- **MACD Cross** (sensitive to momentum changes)

**Best for:** Bull or bear markets with clear direction

### For Range-Bound Markets
Choose mean-reversion strategies:
- **RSI Reversal** (effective in sideways markets)
- **Bollinger Breakout** (captures volatility breakouts)

**Best for:** Consolidation periods, low volatility

### For High Volatility
Choose momentum strategies:
- **KDJ Cross** (responsive to quick changes)
- **MACD Cross** (captures momentum shifts)

**Best for:** High volatility periods, quick moves

### For Low Volatility
Choose patient strategies:
- **Morning Star** (waits for pattern confirmation)
- **MA Cross** (smoother signals)

**Best for:** Stable markets, quality over quantity

## Strategy Combination (Future Feature)

Currently, Stock Pal supports running one strategy at a time. Future versions will support:
- **Multi-strategy portfolios**: Run multiple strategies on different stocks
- **Strategy voting**: Combine signals from multiple strategies
- **Strategy rotation**: Switch strategies based on market conditions

See `/doc/backlog/` for planned enhancements.

## Adding New Strategies

If you're implementing a new strategy:

1. **Create strategy documentation** in this folder:
   - Follow the template below
   - Include all required sections
   - Provide clear examples

2. **Create parameter documentation** in `/doc/strategy_params/`:
   - Document all parameters
   - Provide default values and ranges
   - Include tuning guidance

3. **Implement strategy class** in `/backend/app/services/strategy_service.py`:
   - Follow the strategy interface
   - Implement `generate_signals()` method
   - Add required indicator calculations

4. **Register strategy** in strategy registry:
   - Add to available strategies list
   - Include metadata (name, description, category)

5. **Write tests** in `/backend/tests/`:
   - Test signal generation
   - Test edge cases
   - Test parameter validation

## Strategy Documentation Template

```markdown
# [Strategy Name] Strategy

## Overview

Brief description of the strategy (2-3 sentences).

## Strategy Type

- Category: [Trend-Following / Mean-Reversion / Momentum / Pattern]
- Time Frame: [Short-term / Medium-term / Long-term]
- Risk Level: [Low / Medium / High]

## Technical Indicators Used

- Indicator 1: Brief description
- Indicator 2: Brief description

## Signal Generation Rules

### Buy Signal

Generated when:
1. Condition 1
2. Condition 2
3. ...

**Example:**
When condition X and condition Y are met...

### Sell Signal

Generated when:
1. Condition 1
2. Condition 2
3. ...

**Example:**
When condition Z occurs...

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| param1 | 20 | 5-100 | Description |
| param2 | 70 | 50-90 | Description |

See [strategy_params/[name]_params.md](../strategy_params/[name]_params.md) for detailed parameter documentation.

## Strengths

- Strength 1
- Strength 2
- ...

## Weaknesses

- Weakness 1
- Weakness 2
- ...

## Best Used When

- Market condition 1
- Market condition 2
- ...

## Avoid When

- Market condition 1
- Market condition 2
- ...

## Example Usage

### Scenario 1: [Description]

**Stock:** Example stock
**Period:** Date range
**Parameters:** param1=X, param2=Y
**Result:** Brief summary

### Scenario 2: [Description]

...

## Tips & Best Practices

- Tip 1
- Tip 2
- ...

## Related Strategies

- Strategy A: How they relate
- Strategy B: How they differ

## References

- Academic paper / book / article
- External resources
```

## Performance Expectations

**Important:** Past performance doesn't guarantee future results. These strategies are tools, not guarantees.

**Realistic expectations:**
- No strategy wins 100% of the time
- Win rates typically range 40-60%
- Focus on risk-adjusted returns, not just total return
- Different strategies perform better in different market conditions

**Evaluation metrics:**
- Total return
- Win rate
- Maximum drawdown
- Sharpe ratio (if available)
- Profit factor

## Related Documentation

- **Strategy Parameters** (`/doc/strategy_params/`): Detailed parameter specifications
- **Technical Indicators** (`/doc/散户常用技术指标与交易方法论.md`): Indicator reference
- **API Documentation** (`/doc/api/`): How to use strategies via API
- **Backlog** (`/doc/backlog/`): Future strategy enhancements

## Resources

**Learning More:**
- Read `/doc/散户常用技术指标与交易方法论.md` for technical analysis fundamentals
- Study `/doc/requirements/competitor_analysis.md` to see how other platforms implement strategies
- Check `/doc/backlog/ai_optimization.md` for future AI-powered strategy optimization

**Questions?**
- See main documentation: `/doc/README.md`
- Check API docs: `/doc/api/backtest_engine_v2_usage.md`

---

**Disclaimer:** All strategies are for educational and backtesting purposes only. Use at your own risk in live trading.
