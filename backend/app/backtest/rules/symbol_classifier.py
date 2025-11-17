"""
股票代码分类器

根据股票代码和名称，自动识别市场和板块。
支持中国A股、港股、美股等多市场。
"""

import re
from typing import Tuple, Optional
import logging

from ..models import TradingEnvironment

logger = logging.getLogger(__name__)


class SymbolClassifier:
    """
    股票代码分类器

    功能：
    1. 根据股票代码识别市场（CN, HK, US）
    2. 根据股票代码识别板块（MAIN, GEM, STAR, BSE）
    3. 根据股票名称识别特殊类型（ST）
    4. 生成 TradingEnvironment 对象

    规则映射：
    - 中国A股：
      - 6xxxxx: 上海主板
      - 000xxx, 001xxx: 深圳主板
      - 30xxxx: 创业板
      - 688xxx: 科创板
      - 43xxxx, 83xxxx, 87xxxx: 北交所
    - 香港：
      - xxxxx (5位数字): 港股
    - 美国：
      - 字母代码: 美股
    """

    # 股票代码匹配规则
    # 格式: (正则表达式, 市场, 板块)
    # 注意：特殊板块（科创板、创业板）必须放在主板之前，避免被主板规则误匹配
    PATTERNS = [
        # ========== 中国A股 ==========
        # 科创板（必须在上海主板之前）
        (r'^688\d{3}$', 'CN', 'STAR'),
        # 带交易所后缀的科创板（上交所 .SH）
        (r'^688\d{3}\.SH$', 'CN', 'STAR'),
        # 创业板（必须在深圳主板之前）
        (r'^30[01]\d{3}$', 'CN', 'GEM'),
        # 带交易所后缀的创业板（深交所 .SZ）
        (r'^30[01]\d{3}\.SZ$', 'CN', 'GEM'),
        # 北交所
        (r'^(43|83|87)\d{4}$', 'CN', 'BSE'),
        # 带交易所后缀的北交所（北交所常见 .BJ）
        (r'^(43|83|87)\d{4}\.BJ$', 'CN', 'BSE'),
        # 上海主板
        (r'^6\d{5}$', 'CN', 'MAIN'),
        # 带交易所后缀的上海主板
        (r'^6\d{5}\.SH$', 'CN', 'MAIN'),
        # 深圳主板
        (r'^00[01]\d{3}$', 'CN', 'MAIN'),
        # 带交易所后缀的深圳主板
        (r'^00[01]\d{3}\.SZ$', 'CN', 'MAIN'),

        # ========== 香港 ==========
        # 港股（5位数字，可能带.HK后缀）
        (r'^\d{5}$', 'HK', 'MAIN'),
        (r'^\d{5}\.HK$', 'HK', 'MAIN'),

        # ========== 美国 ==========
        # 美股（1-5个大写字母）
        (r'^[A-Z]{1,5}$', 'US', 'NYSE'),
    ]

    @classmethod
    def classify(cls, symbol: str) -> Tuple[str, str]:
        """
        分类股票代码

        Args:
            symbol: 股票代码

        Returns:
            (market, board): 市场和板块代码
                例如: ('CN', 'GEM')

        Raises:
            ValueError: 无法识别的股票代码
        """
        # 清理代码（去除空格等）
        symbol = symbol.strip().upper()

        for pattern, market, board in cls.PATTERNS:
            if re.match(pattern, symbol):
                logger.debug(f"Classified {symbol} as {market}_{board}")
                return market, board

        raise ValueError(f"Cannot classify symbol: {symbol}")

    @classmethod
    def is_st_stock(cls, stock_name: str) -> bool:
        """
        判断是否为ST股票

        Args:
            stock_name: 股票名称

        Returns:
            bool: 是否为ST股票
        """
        if not stock_name:
            return False

        # ST 标识：ST、*ST、S*ST、SST等
        st_patterns = [
            r'\*ST',    # *ST
            r'ST',      # ST
            r'S\*ST',   # S*ST
            r'SST',     # SST
        ]

        for pattern in st_patterns:
            if re.search(pattern, stock_name):
                return True

        return False

    @classmethod
    def detect_board_override(
        cls,
        symbol: str,
        stock_name: Optional[str],
        market: str,
        board: str
    ) -> str:
        """
        检测板块覆盖

        某些特殊股票（如ST）需要使用特殊的交易规则，
        覆盖原有板块分类。

        Args:
            symbol: 股票代码
            stock_name: 股票名称
            market: 市场
            board: 原始板块

        Returns:
            str: 最终板块（可能被覆盖）
        """
        # 只有中国A股有ST规则
        if market == 'CN' and stock_name and cls.is_st_stock(stock_name):
            logger.debug(f"Stock {symbol} ({stock_name}) identified as ST, "
                        f"overriding board from {board} to ST")
            return 'ST'

        return board

    @classmethod
    def get_trading_environment(
        cls,
        symbol: str,
        stock_name: Optional[str] = None,
        channel: str = 'DIRECT'
    ) -> TradingEnvironment:
        """
        获取交易环境

        Args:
            symbol: 股票代码
            stock_name: 股票名称（用于ST判断）
            channel: 交易渠道（DIRECT, CONNECT等）

        Returns:
            TradingEnvironment: 交易环境对象

        Example:
            >>> env = SymbolClassifier.get_trading_environment('600000')
            >>> print(env)
            TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')

            >>> env = SymbolClassifier.get_trading_environment('300001')
            >>> print(env)
            TradingEnvironment(market='CN', board='GEM', channel='DIRECT')

            >>> env = SymbolClassifier.get_trading_environment(
            ...     '600001', stock_name='*ST华电', channel='DIRECT'
            ... )
            >>> print(env)
            TradingEnvironment(market='CN', board='ST', channel='DIRECT')
        """
        # 识别市场和板块
        market, board = cls.classify(symbol)

        # 检测板块覆盖（如ST）
        board = cls.detect_board_override(symbol, stock_name, market, board)

        # 创建交易环境
        return TradingEnvironment(
            market=market,
            board=board,
            channel=channel
        )

    @classmethod
    def get_board_name(cls, board: str) -> str:
        """
        获取板块中文名称

        Args:
            board: 板块代码

        Returns:
            str: 板块中文名称
        """
        board_names = {
            'MAIN': '主板',
            'GEM': '创业板',
            'STAR': '科创板',
            'BSE': '北交所',
            'ST': 'ST股票',
            'HK_MAIN': '港股主板',
            'US_NYSE': '纽交所',
            'US_NASDAQ': '纳斯达克',
        }
        return board_names.get(board, board)

    @classmethod
    def get_market_name(cls, market: str) -> str:
        """
        获取市场中文名称

        Args:
            market: 市场代码

        Returns:
            str: 市场中文名称
        """
        market_names = {
            'CN': '中国A股',
            'HK': '香港',
            'US': '美国',
        }
        return market_names.get(market, market)

    @classmethod
    def format_symbol(cls, symbol: str, market: Optional[str] = None) -> str:
        """
        格式化股票代码

        根据市场规范格式化股票代码（如补齐0、添加后缀等）

        Args:
            symbol: 原始股票代码
            market: 市场代码（如果已知）

        Returns:
            str: 格式化后的股票代码
        """
        symbol = symbol.strip().upper()

        # 如果市场未知，先识别
        if market is None:
            try:
                market, _ = cls.classify(symbol)
            except ValueError:
                return symbol

        # 中国A股：确保6位数字
        if market == 'CN':
            # 去除可能的前缀（如SZ、SH）
            symbol = re.sub(r'^(SZ|SH)', '', symbol)
            # 如果不足6位，补0
            if symbol.isdigit() and len(symbol) < 6:
                symbol = symbol.zfill(6)

        # 港股：去除.HK后缀
        elif market == 'HK':
            symbol = symbol.replace('.HK', '')
            # 确保5位数字
            if symbol.isdigit() and len(symbol) < 5:
                symbol = symbol.zfill(5)

        return symbol


def classify_symbol(symbol: str, stock_name: Optional[str] = None) -> TradingEnvironment:
    """
    便捷函数：分类股票代码并返回交易环境

    Args:
        symbol: 股票代码
        stock_name: 股票名称（可选）

    Returns:
        TradingEnvironment: 交易环境

    Example:
        >>> env = classify_symbol('600000')
        >>> print(env)
        CN_MAIN
    """
    return SymbolClassifier.get_trading_environment(symbol, stock_name)
