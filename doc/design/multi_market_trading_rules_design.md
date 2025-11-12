# 多市场交易规则架构设计

**创建时间**: 2025-11-12
**状态**: 设计中

---

## 设计目标

构建支持多市场、多板块、多渠道的交易规则系统，准确建模以下场景：

1. **A股板块差异**：主板±10%、创业板±20%、科创板±20%、北交所±30%、ST±5%
2. **港股通特殊性**：T+0交易但T+2资金交割、港股规则+A股渠道费用
3. **未来扩展**：美股盘前/盘后、期权期货、其他市场

---

## 核心架构：三层模型

### 三层模型

```
┌────────────────────────────────────────────┐
│           Market (市场)                     │
│  CN (中国), HK (香港), US (美国)             │
└──────────────┬─────────────────────────────┘
               │
        ┌──────▼──────┐
        │  Board (板块) │
        │ MAIN, GEM,   │
        │ STAR, BSE    │
        └──────┬───────┘
               │
        ┌──────▼──────────┐
        │ Channel (渠道)   │
        │ DIRECT, CONNECT │
        └─────────────────┘
```

### 层级定义

#### Layer 1: Market（市场）
**定义**：宏观的地理/监管区域

```python
class Market(Enum):
    CN = 'CN'      # 中国大陆
    HK = 'HK'      # 香港
    US = 'US'      # 美国
    SG = 'SG'      # 新加坡
```

#### Layer 2: Board（板块/板）
**定义**：交易所内的细分市场

```python
class Board(Enum):
    # 中国大陆板块
    CN_MAIN = 'CN_MAIN'          # 主板（沪深）
    CN_GEM = 'CN_GEM'            # 创业板
    CN_STAR = 'CN_STAR'          # 科创板
    CN_BSE = 'CN_BSE'            # 北交所
    CN_ST = 'CN_ST'              # ST股票

    # 香港板块
    HK_MAIN = 'HK_MAIN'          # 港股主板
    HK_GEM = 'HK_GEM'            # 创业板

    # 美国板块
    US_NYSE = 'US_NYSE'          # 纽交所
    US_NASDAQ = 'US_NASDAQ'      # 纳斯达克
```

#### Layer 3: Channel（交易渠道）
**定义**：投资者接入市场的方式

```python
class Channel(Enum):
    DIRECT = 'DIRECT'            # 直接交易（开通当地账户）
    CONNECT = 'CONNECT'          # 互联互通（如沪深港通）
    QDII = 'QDII'                # QDII基金通道
    QFII = 'QFII'                # QFII通道
```

---

## 核心设计

### 1. 交易环境（TradingEnvironment）

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TradingEnvironment:
    """交易环境：市场+板块+渠道的组合"""

    market: str           # 市场：CN, HK, US
    board: str            # 板块：MAIN, GEM, STAR, ...
    channel: str = 'DIRECT'  # 渠道：DIRECT, CONNECT, ...

    def __str__(self):
        """生成唯一标识符"""
        if self.channel == 'DIRECT':
            return f"{self.market}_{self.board}"
        else:
            return f"{self.market}_{self.board}_{self.channel}"

    @classmethod
    def from_symbol(cls, symbol: str, hint: Optional[dict] = None):
        """从股票代码推断交易环境"""
        # 1. 识别市场和板块
        market, board = SymbolClassifier.classify(symbol)

        # 2. 渠道默认为DIRECT，除非用户明确指定
        channel = hint.get('channel', 'DIRECT') if hint else 'DIRECT'

        return cls(market=market, board=board, channel=channel)


# 示例使用
env1 = TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')
# str: "CN_MAIN"

env2 = TradingEnvironment(market='HK', board='MAIN', channel='CONNECT')
# str: "HK_MAIN_CONNECT" (港股通)

env3 = TradingEnvironment(market='CN', board='GEM', channel='DIRECT')
# str: "CN_GEM"
```

### 2. 分层规则（Layered Rules）

```python
class TradingRules:
    """交易规则组合器"""

    def __init__(self, environment: TradingEnvironment):
        self.environment = environment

        # 加载各层规则
        self.market_rules = self._load_market_rules(environment.market)
        self.board_rules = self._load_board_rules(environment.market, environment.board)
        self.channel_rules = self._load_channel_rules(environment.channel)

    def _load_market_rules(self, market: str):
        """加载市场基础规则"""
        config = load_config(f"config/markets/{market.lower()}/base.yaml")
        return MarketBaseRules(config)

    def _load_board_rules(self, market: str, board: str):
        """加载板块特定规则"""
        config = load_config(f"config/markets/{market.lower()}/boards/{board.lower()}.yaml")
        return BoardRules(config)

    def _load_channel_rules(self, channel: str):
        """加载渠道规则（装饰器模式）"""
        if channel == 'DIRECT':
            return None  # 直接交易无额外规则
        config = load_config(f"config/channels/{channel.lower()}.yaml")
        return ChannelRules(config)

    def validate_order(self, order, market_data, portfolio, context) -> ValidationResult:
        """验证订单（组合各层规则）"""
        errors = []

        # 1. 市场基础规则
        result = self.market_rules.validate(order, market_data, portfolio, context)
        if not result.is_valid:
            errors.extend(result.errors)

        # 2. 板块特定规则
        result = self.board_rules.validate(order, market_data, portfolio, context)
        if not result.is_valid:
            errors.extend(result.errors)

        # 3. 渠道规则（如果有）
        if self.channel_rules:
            result = self.channel_rules.validate(order, market_data, portfolio, context)
            if not result.is_valid:
                errors.extend(result.errors)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def get_price_limits(self, prev_close: float, stock_info: StockInfo) -> PriceLimits:
        """获取涨跌停价格（板块规则）"""
        # 板块规则决定涨跌停
        return self.board_rules.get_price_limits(prev_close, stock_info)

    def get_commission(self, amount: float, side: OrderSide, stock_info: StockInfo) -> Commission:
        """计算费用（市场+渠道）"""
        # 市场基础费用
        base_commission = self.market_rules.get_commission(amount, side, stock_info)

        # 渠道额外费用
        if self.channel_rules:
            channel_fee = self.channel_rules.get_additional_commission(amount, side)
            base_commission.total += channel_fee

        return base_commission

    def get_settlement_period(self) -> int:
        """获取交割周期（市场基础规则）"""
        return self.market_rules.get_settlement_period()
```

### 3. 规则工厂（增强版）

```python
class TradingRulesFactory:
    """交易规则工厂（支持分层）"""

    _cache: Dict[str, TradingRules] = {}

    @classmethod
    def get_rules(cls, environment: TradingEnvironment) -> TradingRules:
        """获取交易规则实例"""
        env_key = str(environment)

        if env_key not in cls._cache:
            cls._cache[env_key] = TradingRules(environment)

        return cls._cache[env_key]

    @classmethod
    def get_rules_for_symbol(cls, symbol: str, hint: Optional[dict] = None) -> TradingRules:
        """根据股票代码获取规则"""
        environment = TradingEnvironment.from_symbol(symbol, hint)
        return cls.get_rules(environment)


# 使用示例
# 1. A股主板（直接交易）
rules = TradingRulesFactory.get_rules_for_symbol('600000')
# environment: CN_MAIN_DIRECT

# 2. A股创业板（直接交易）
rules = TradingRulesFactory.get_rules_for_symbol('300001')
# environment: CN_GEM_DIRECT

# 3. 港股通
rules = TradingRulesFactory.get_rules_for_symbol('00700', hint={'channel': 'CONNECT'})
# environment: HK_MAIN_CONNECT

# 4. 直接港股交易
rules = TradingRulesFactory.get_rules_for_symbol('00700', hint={'channel': 'DIRECT'})
# environment: HK_MAIN_DIRECT
```

---

## 配置文件设计

### 目录结构

```
config/
├── markets/                    # 市场配置
│   ├── cn/                     # 中国大陆
│   │   ├── base.yaml           # 市场基础规则（T+1、费用基础）
│   │   └── boards/             # 板块规则
│   │       ├── main.yaml       # 主板：±10%
│   │       ├── gem.yaml        # 创业板：±20%，前5日无涨跌停
│   │       ├── star.yaml       # 科创板：±20%，前5日无涨跌停
│   │       ├── bse.yaml        # 北交所：±30%
│   │       └── st.yaml         # ST：±5%
│   │
│   ├── hk/                     # 香港
│   │   ├── base.yaml           # 市场基础规则（T+2、无涨跌停）
│   │   └── boards/
│   │       ├── main.yaml       # 主板
│   │       └── gem.yaml        # 创业板
│   │
│   └── us/                     # 美国
│       ├── base.yaml
│       └── boards/
│           ├── nyse.yaml
│           └── nasdaq.yaml
│
└── channels/                   # 渠道配置
    ├── direct.yaml             # 直接交易（无额外规则）
    ├── connect.yaml            # 沪深港通
    └── qdii.yaml               # QDII
```

### 配置示例

#### 1. 中国市场基础规则
**`config/markets/cn/base.yaml`**

```yaml
market_id: CN
market_name: 中国A股
timezone: Asia/Shanghai
currency: CNY

# 基础交易规则
trading_rules:
  settlement_period: 1        # T+1
  lot_size: 100              # 100股为1手
  short_selling: false       # 普通账户不允许卖空

  trading_hours:
    morning:
      start: "09:30"
      end: "11:30"
    afternoon:
      start: "13:00"
      end: "15:00"

# 基础费用
commission:
  broker_rate: 0.0003         # 券商佣金 0.03%
  min_broker_fee: 5.0         # 最低佣金 5元
  stamp_tax_rate: 0.001       # 印花税 0.1%（仅卖出）
  transfer_fee_rate: 0.00002  # 过户费 0.002%（仅上海）
```

#### 2. 创业板特定规则
**`config/markets/cn/boards/gem.yaml`**

```yaml
board_id: GEM
board_name: 创业板
stock_code_pattern: '^30\d{4}$'  # 300xxx, 301xxx

# 涨跌停规则
price_limits:
  default:
    up_limit_pct: 0.20        # +20%
    down_limit_pct: 0.20      # -20%

  ipo_exception:              # 新股上市特殊规则
    first_n_days: 5           # 前5个交易日
    up_limit_pct: null        # 无涨跌停限制
    down_limit_pct: null

# 交易权限
authorization_required: true
authorization_type: 'GEM_TRADING'

# 盘后交易
after_hours_trading:
  enabled: true
  time_range:
    start: "15:05"
    end: "15:30"
```

#### 3. 主板规则
**`config/markets/cn/boards/main.yaml`**

```yaml
board_id: MAIN
board_name: 主板
stock_code_pattern: '^(6|0|9)\d{5}$'  # 6xxxxx, 000xxx, 900xxx

price_limits:
  default:
    up_limit_pct: 0.10        # +10%
    down_limit_pct: 0.10      # -10%

  ipo_exception:
    first_n_days: 1
    up_limit_pct: 0.44        # 首日44%

authorization_required: false

after_hours_trading:
  enabled: false
```

#### 4. 港股通渠道规则
**`config/channels/connect.yaml`**

```yaml
channel_id: CONNECT
channel_name: 沪深港通

# 适用市场
applicable_markets:
  - market: HK
    boards: [MAIN]  # 只能交易港股主板

# 交易规则叠加
trading_rules:
  settlement_period: 2        # 资金T+2交割（虽然日内T+0）
  day_trading: true           # 允许日内交易（T+0）

  # 额外限制
  restrictions:
    - 每日额度限制
    - 只能交易标的范围内股票（恒生大中型股）
    - 不支持碎股交易

# 费用叠加
commission:
  currency_conversion_fee: 0.0001  # 货币兑换费 0.01%
  settlement_fee_rate: 0.00002     # 额外结算费

# 交易日历
trading_days:
  require_both_open: true     # 沪深和港股都开市才能交易
  markets: [CN, HK]
```

---

## 股票代码分类器（增强版）

```python
class SymbolClassifier:
    """股票代码分类器（识别市场和板块）"""

    # 规则映射
    PATTERNS = [
        # 中国大陆
        (r'^6\d{5}$', 'CN', 'MAIN'),           # 上海主板
        (r'^000\d{3}$', 'CN', 'MAIN'),         # 深圳主板
        (r'^001\d{3}$', 'CN', 'MAIN'),         # 深圳主板
        (r'^30[01]\d{3}$', 'CN', 'GEM'),       # 创业板
        (r'^688\d{3}$', 'CN', 'STAR'),         # 科创板
        (r'^(43|83|87)\d{4}$', 'CN', 'BSE'),   # 北交所

        # 香港
        (r'^\d{5}$', 'HK', 'MAIN'),            # 港股（需要上下文）
        (r'^\d{5}\.HK$', 'HK', 'MAIN'),

        # 美国
        (r'^[A-Z]{1,5}$', 'US', 'NYSE'),       # 默认纽交所
    ]

    @classmethod
    def classify(cls, symbol: str) -> Tuple[str, str]:
        """
        分类股票代码

        Returns:
            (market, board): 如 ('CN', 'GEM')
        """
        for pattern, market, board in cls.PATTERNS:
            if re.match(pattern, symbol):
                return market, board

        raise ValueError(f"Cannot classify symbol: {symbol}")

    @classmethod
    def is_st_stock(cls, stock_name: str) -> bool:
        """判断是否为ST股票"""
        return 'ST' in stock_name or '*ST' in stock_name

    @classmethod
    def detect_board_override(cls, symbol: str, stock_name: str, market: str, board: str) -> str:
        """
        检测板块覆盖（如ST股票）

        Returns:
            board: 可能被覆盖的板块
        """
        if market == 'CN' and cls.is_st_stock(stock_name):
            return 'ST'  # ST股票有特殊规则，覆盖原板块
        return board
```

---

## 使用场景示例

### 场景1: A股创业板直接交易

```python
# 股票代码
symbol = '300001'

# 自动识别环境
env = TradingEnvironment.from_symbol(symbol)
# env: TradingEnvironment(market='CN', board='GEM', channel='DIRECT')

# 获取规则
rules = TradingRulesFactory.get_rules(env)

# 验证涨跌停
price_limits = rules.get_price_limits(prev_close=20.0, stock_info)
# PriceLimits(upper=24.0, lower=16.0, has_limit=True)  # ±20%

# 验证订单（创业板需要权限）
validation = rules.validate_order(order, market_data, portfolio, context)
# 可能报错：未开通创业板权限
```

### 场景2: 港股通交易

```python
# 股票代码
symbol = '00700'

# 用户指定渠道为港股通
env = TradingEnvironment.from_symbol(symbol, hint={'channel': 'CONNECT'})
# env: TradingEnvironment(market='HK', board='MAIN', channel='CONNECT')

# 获取规则
rules = TradingRulesFactory.get_rules(env)

# 检查涨跌停
price_limits = rules.get_price_limits(prev_close=300.0, stock_info)
# PriceLimits(upper=None, lower=None, has_limit=False)  # 港股无涨跌停

# 检查交割周期
settlement = rules.get_settlement_period()
# 2  # T+2资金交割（虽然允许T+0交易）

# 费用计算（包含港股通额外费用）
commission = rules.get_commission(amount=30000, side='BUY', stock_info)
# Commission(
#   broker_fee=9.0,        # A股券商佣金
#   stamp_tax=39.0,        # 港股印花税 0.13%
#   transfer_fee=1.7,      # 港股交易费
#   settlement_fee=0.6,    # 港股结算费
#   currency_fee=3.0,      # 港股通货币兑换费（额外）
#   total=53.3
# )
```

### 场景3: 科创板新股前5日

```python
symbol = '688001'

env = TradingEnvironment.from_symbol(symbol)
rules = TradingRulesFactory.get_rules(env)

# 获取股票信息（包含IPO日期）
stock_info = StockInfo(
    symbol='688001',
    name='华兴源创',
    ipo_date='2024-11-10',
    ...
)

# 当前日期
context = TradingContext(current_date=datetime(2024, 11, 12))  # IPO后第2天

# 检查涨跌停
price_limits = rules.get_price_limits(prev_close=50.0, stock_info)
# PriceLimits(upper=None, lower=None, has_limit=False)  # 前5日无涨跌停

# 如果是第6天
context = TradingContext(current_date=datetime(2024, 11, 16))
price_limits = rules.get_price_limits(prev_close=60.0, stock_info)
# PriceLimits(upper=72.0, lower=48.0, has_limit=True)  # ±20%
```

---

## 架构优势

### 优势

1. **精确建模现实**：
   - ✅ 准确表达港股通等混合渠道
   - ✅ 区分不同板块规则
   - ✅ 易于扩展新渠道

2. **配置灵活**：
   - ✅ 三层配置可独立修改
   - ✅ 规则组合清晰
   - ✅ 复用市场基础配置

3. **易于理解**：
   - ✅ 层级清晰（市场→板块→渠道）
   - ✅ 符合现实结构
   - ✅ 文档友好

### 实现注意事项

1. **性能优化**：
   - 规则实例需要缓存（工厂模式）
   - 配置文件在启动时加载
   - 避免重复解析YAML

2. **配置管理**：
   - 配置文件分层清晰
   - 命名规范统一
   - 提供配置校验工具

---

## 实施建议

### Phase 1: 核心架构（1周）
1. 实现 `TradingEnvironment` 类
2. 实现分层规则加载器
3. 实现 `SymbolClassifier` 增强版
4. 单元测试

### Phase 2: 配置文件（3天）
1. 创建目录结构
2. 编写A股各板块配置
3. 编写港股配置
4. 编写港股通渠道配置

### Phase 3: 集成测试（2天）
1. A股主板、创业板、科创板测试
2. 港股通测试
3. 边界情况测试（ST、新股、停牌）

### Phase 4: 文档与部署（1天）
1. 编写使用文档
2. 配置部署脚本
3. 测试数据准备

---

**总结**：三层架构能够精确建模港股通等复杂场景，并为未来扩展打下良好基础。
