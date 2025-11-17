"""
每手股数（Lot Size）规则

定义不同市场和股票的交易单位（一手多少股）。

规则：
- 中国A股：100股/手（统一规定）
- 香港：每只股票不同，常见有100、200、400、500、1000等
- 美国：1股（无整手限制）
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LotSizeRules:
    """
    每手股数规则

    管理不同市场和股票的交易单位。
    """

    # 港股常见股票的每手股数（根据实际情况扩展）
    # 格式: {股票代码: 每手股数}
    HK_STOCK_LOT_SIZES = {
        # 互联网科技
        '00700': 100,  # 腾讯控股
        '09988': 100,  # 阿里巴巴-SW
        '03690': 100,  # 美团-W
        '01810': 200,  # 小米集团-W
        '09618': 100,  # 京东集团-SW
        '01024': 100,  # 快手-W
        '09999': 100,  # 网易-S
        '09888': 100,  # 百度集团-SW
        '09626': 100,  # 哔哩哔哩-W
        '09961': 100,  # 携程集团-S
        # 金融
        '00005': 400,  # 汇丰控股
        '00941': 500,  # 中国移动
        '01398': 1000, # 工商银行
        '03988': 500,  # 中国银行
        '01288': 500,  # 农业银行
        '00939': 500,  # 建设银行
        # 可以继续添加更多股票...
    }

    # 默认每手股数（市场级别）
    DEFAULT_LOT_SIZES = {
        'CN': 100,    # 中国A股：100股/手
        'HK': 100,    # 港股默认：100股/手（如果未在HK_STOCK_LOT_SIZES中找到）
        'US': 1,      # 美股：1股（无整手限制）
    }

    @classmethod
    def get_lot_size(cls, symbol: str, market: str) -> int:
        """
        获取指定股票的每手股数

        Args:
            symbol: 股票代码（已清理，无后缀）
            market: 市场代码（CN, HK, US）

        Returns:
            int: 每手股数

        Example:
            >>> LotSizeRules.get_lot_size('600000', 'CN')
            100
            >>> LotSizeRules.get_lot_size('01810', 'HK')
            200
            >>> LotSizeRules.get_lot_size('AAPL', 'US')
            1
        """
        # 清理股票代码（去除.HK等后缀）
        clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')

        # 港股：查找特定股票的每手股数
        if market == 'HK':
            # 确保5位数字格式
            if clean_symbol.isdigit():
                clean_symbol = clean_symbol.zfill(5)

            lot_size = cls.HK_STOCK_LOT_SIZES.get(clean_symbol)
            if lot_size:
                logger.debug(f"Found lot size for {symbol}: {lot_size} shares/lot")
                return lot_size

        # 使用市场默认值
        default_lot_size = cls.DEFAULT_LOT_SIZES.get(market, 100)
        logger.debug(f"Using default lot size for {symbol} ({market}): {default_lot_size} shares/lot")
        return default_lot_size

    @classmethod
    def round_to_lot(cls, quantity: int, lot_size: int) -> int:
        """
        将数量向下取整到整手

        Args:
            quantity: 原始数量
            lot_size: 每手股数

        Returns:
            int: 取整后的数量（整手）

        Example:
            >>> LotSizeRules.round_to_lot(250, 100)
            200
            >>> LotSizeRules.round_to_lot(350, 200)
            200
        """
        if lot_size <= 0:
            raise ValueError(f"Invalid lot_size: {lot_size}")

        return (quantity // lot_size) * lot_size

    @classmethod
    def add_stock_lot_size(cls, symbol: str, lot_size: int):
        """
        添加港股股票的每手股数

        用于动态添加新股票的lot size信息

        Args:
            symbol: 股票代码（5位数字，无后缀）
            lot_size: 每手股数
        """
        clean_symbol = symbol.replace('.HK', '').zfill(5)
        cls.HK_STOCK_LOT_SIZES[clean_symbol] = lot_size
        logger.info(f"Added lot size for {clean_symbol}: {lot_size} shares/lot")


def get_lot_size(symbol: str, market: str) -> int:
    """
    便捷函数：获取指定股票的每手股数

    Args:
        symbol: 股票代码
        market: 市场代码（CN, HK, US）

    Returns:
        int: 每手股数
    """
    return LotSizeRules.get_lot_size(symbol, market)
