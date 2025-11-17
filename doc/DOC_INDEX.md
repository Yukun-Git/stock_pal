# Stock Pal Documentation Index

Last updated: 2025-11-14

## Overview

This index provides a complete directory of all documentation in the Stock Pal project. The documentation is organized by category to help you quickly find relevant information.

## Documentation Statistics

- Total documents: 44
- Last 7 days updates: 20
- Documentation categories: 10

## Directory Structure

```
doc/
├── api/              # API usage documentation and guides
├── backlog/          # Future feature ideas and enhancements
├── brainstorm/       # Analysis and exploratory documents
├── design/           # Feature design documents
│   └── done/         # Completed design documents
├── development/      # Development progress tracking
│   ├── done/         # Completed development summaries
│   └── progress/     # In-progress development tracking
├── plan/             # Project planning and feature breakdown
├── requirements/     # Product requirements and roadmap
├── strategy/         # Trading strategy documentation
└── strategy_params/  # Strategy parameter specifications
```

## Quick Navigation

### Getting Started
- [Product Requirements](requirements/product_requirements_stock_pal.md) - Core product vision and requirements
- [Product Roadmap](requirements/product_roadmap.md) - Development timeline and milestones
- [Feature Breakdown](plan/feature_breakdown.md) - Detailed feature decomposition
- [Competitor Analysis](requirements/competitor_analysis.md) - Market analysis

### For Developers
- [API Documentation](api/backtest_engine_v2_usage.md) - Backtest Engine V2 API usage
- [Design Documents](design/) - Current and completed design specs
- [Development Progress](development/progress/) - Active development tracking

### For Strategy Development
- [Strategy Documentation](strategy/) - All implemented trading strategies
- [Strategy Parameters](strategy_params/) - Parameter specifications for each strategy
- [Technical Indicators Guide](散户常用技术指标与交易方法论.md) - Reference for technical analysis

### Future Planning
- [Backlog Overview](backlog/README.md) - All future features overview
- [Feature Ideas](backlog/) - Detailed backlog items

---

## Documents by Category

### API Documentation (doc/api/)

- [backtest_engine_v2_usage.md](api/backtest_engine_v2_usage.md) - Backtest Engine V2 API usage guide and examples

### Backlog - Future Features (doc/backlog/)

Overview and high-priority items:
- [README.md](backlog/README.md) - Backlog overview and categorization

**Core Trading Enhancements:**
- [position_management.md](backlog/position_management.md) - Position sizing and management features
- [market_adaptive_configuration.md](backlog/market_adaptive_configuration.md) - Market-adaptive strategy configuration
- [backtest_history_storage.md](backlog/backtest_history_storage.md) - Backtest result storage and comparison

**AI & Optimization:**
- [ai_optimization.md](backlog/ai_optimization.md) - AI-powered strategy optimization
- [enterprise_reputation_quantification.md](backlog/enterprise_reputation_quantification.md) - Company reputation scoring

**Configuration & Marketplace:**
- [configuration_management.md](backlog/configuration_management.md) - Strategy configuration management
- [configuration_marketplace.md](backlog/configuration_marketplace.md) - Configuration sharing marketplace

**Community & Gamification:**
- [strategy_arena.md](backlog/strategy_arena.md) - Strategy competition platform
- [gamification.md](backlog/gamification.md) - Gamification features
- [social_learning.md](backlog/social_learning.md) - Social learning and collaboration

**User System:**
- [user_account_system.md](backlog/user_account_system.md) - User authentication and account management

### Brainstorm & Analysis (doc/brainstorm/)

- [complete_trading_system_analysis.md](brainstorm/complete_trading_system_analysis.md) - Comprehensive trading system analysis

### Design Documents (doc/design/)

**Active Design:**
- [backtest_post_mvp_enhancements.md](design/backtest_post_mvp_enhancements.md) - Post-MVP backtest enhancements
- [risk_manager_detailed_design.md](design/risk_manager_detailed_design.md) - Risk manager detailed design
- [risk_manager_frontend_design.md](design/risk_manager_frontend_design.md) - Risk manager frontend design

**Completed Design (doc/design/done/):**
- [backtest_engine_upgrade_design.md](design/done/backtest_engine_upgrade_design.md) - Backtest engine upgrade design
- [frontend_metrics_enhancement_design.md](design/done/frontend_metrics_enhancement_design.md) - Frontend metrics enhancement
- [multi_market_trading_rules_design.md](design/done/multi_market_trading_rules_design.md) - Multi-market trading rules

### Development Documentation (doc/development/)

**In Progress (doc/development/progress/):**
- [backtest_engine_upgrade_progress.md](development/progress/backtest_engine_upgrade_progress.md) - Backtest engine upgrade status
- [strategy-documentation-feature.md](development/progress/strategy-documentation-feature.md) - Strategy documentation feature status

**Completed (doc/development/done/):**
- [backend_refactoring_summary.md](development/done/backend_refactoring_summary.md) - Backend refactoring summary
- [frontend_refactoring_plan.md](development/done/frontend_refactoring_plan.md) - Frontend refactoring plan
- [frontend_refactoring_summary.md](development/done/frontend_refactoring_summary.md) - Frontend refactoring summary
- [risk_manager_frontend_complete_summary.md](development/done/risk_manager_frontend_complete_summary.md) - Risk manager complete summary
- [risk_manager_frontend_phase1_summary.md](development/done/risk_manager_frontend_phase1_summary.md) - Phase 1 summary
- [risk_manager_frontend_phase2_summary.md](development/done/risk_manager_frontend_phase2_summary.md) - Phase 2 summary
- [risk_manager_frontend_phase3_summary.md](development/done/risk_manager_frontend_phase3_summary.md) - Phase 3 summary
- [多策略组合功能开发进度.md](development/done/多策略组合功能开发进度.md) - Multi-strategy combination progress

### Planning (doc/plan/)

- [feature_breakdown.md](plan/feature_breakdown.md) - Detailed feature breakdown and prioritization

### Requirements (doc/requirements/)

- [competitor_analysis.md](requirements/competitor_analysis.md) - Competitor analysis and market positioning
- [product_requirements_stock_pal.md](requirements/product_requirements_stock_pal.md) - Core product requirements document
- [product_roadmap.md](requirements/product_roadmap.md) - Product development roadmap

### Trading Strategies (doc/strategy/)

All implemented trading strategies:
- [boll_breakout.md](strategy/boll_breakout.md) - Bollinger Bands breakout strategy
- [kdj_cross.md](strategy/kdj_cross.md) - KDJ indicator crossover strategy
- [ma_cross.md](strategy/ma_cross.md) - Moving average crossover strategy
- [macd_cross.md](strategy/macd_cross.md) - MACD crossover strategy
- [morning_star.md](strategy/morning_star.md) - Morning star candlestick pattern strategy
- [rsi_reversal.md](strategy/rsi_reversal.md) - RSI reversal strategy

### Strategy Parameters (doc/strategy_params/)

Parameter specifications for each strategy:
- [boll_breakout_params.md](strategy_params/boll_breakout_params.md) - Bollinger Bands parameters
- [kdj_cross_params.md](strategy_params/kdj_cross_params.md) - KDJ parameters
- [ma_cross_params.md](strategy_params/ma_cross_params.md) - Moving average parameters
- [macd_cross_params.md](strategy_params/macd_cross_params.md) - MACD parameters
- [morning_star_params.md](strategy_params/morning_star_params.md) - Morning star parameters
- [rsi_reversal_params.md](strategy_params/rsi_reversal_params.md) - RSI parameters

### Reference Materials (doc/)

- [散户常用技术指标与交易方法论.md](散户常用技术指标与交易方法论.md) - Technical indicators and trading methodology for retail investors

---

## Recent Updates (Last 7 Days)

- 2025-11-14: [brainstorm/complete_trading_system_analysis.md](brainstorm/complete_trading_system_analysis.md) - New comprehensive analysis
- 2025-11-14: [backlog/README.md](backlog/README.md) - Updated backlog overview
- 2025-11-14: [backlog/position_management.md](backlog/position_management.md) - New position management feature
- 2025-11-14: [backlog/market_adaptive_configuration.md](backlog/market_adaptive_configuration.md) - New adaptive config feature
- 2025-11-14: Multiple backlog items added (social_learning, gamification, ai_optimization, etc.)
- 2025-11-13: Risk manager frontend development completed (4 documents)
- 2025-11-13: [design/risk_manager_frontend_design.md](design/risk_manager_frontend_design.md) - Design finalized
- 2025-11-12: [design/risk_manager_detailed_design.md](design/risk_manager_detailed_design.md) - Detailed design added
- 2025-11-12: [design/backtest_post_mvp_enhancements.md](design/backtest_post_mvp_enhancements.md) - Post-MVP planning

---

## Document Status Legend

- **Backlog**: Future features not yet started
- **Design**: Specification documents for features
- **Design/Done**: Completed and implemented designs
- **Development/Progress**: Currently in development
- **Development/Done**: Completed development work
- **Requirements**: Product-level specifications
- **Plan**: Project planning and breakdown

---

## How to Use This Index

1. **Finding a specific topic**: Use your browser's search (Ctrl/Cmd+F) to search for keywords
2. **Exploring by category**: Browse the "Documents by Category" section
3. **Checking recent activity**: See "Recent Updates" for latest changes
4. **Understanding project status**: Check Development/Progress for active work

## Contributing to Documentation

When adding new documentation:
1. Place documents in the appropriate category folder
2. Follow naming conventions: lowercase with underscores (e.g., `my_feature_design.md`)
3. Update this index by running the doc-manager tool
4. Move completed design/progress docs to respective `done/` folders
5. Add a clear title and description at the top of your document

## Need Help?

- For general questions: See [README.md](README.md)
- For API documentation: See [api/](api/)
- For product context: See [requirements/product_requirements_stock_pal.md](requirements/product_requirements_stock_pal.md)
