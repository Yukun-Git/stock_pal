"""
测试股票代码分类器

测试 symbol_classifier.py 的所有功能
"""

import pytest

from app.backtest.rules.symbol_classifier import SymbolClassifier, classify_symbol
from app.backtest.models import TradingEnvironment


class TestSymbolClassifier:
    """测试股票代码分类器"""

    def test_classify_cn_main_shanghai(self):
        """测试上海主板识别"""
        market, board = SymbolClassifier.classify('600000')
        assert market == 'CN'
        assert board == 'MAIN'

    def test_classify_cn_main_shenzhen(self):
        """测试深圳主板识别"""
        market, board = SymbolClassifier.classify('000001')
        assert market == 'CN'
        assert board == 'MAIN'

        market, board = SymbolClassifier.classify('001001')
        assert market == 'CN'
        assert board == 'MAIN'

    def test_classify_cn_gem(self):
        """测试创业板识别"""
        market, board = SymbolClassifier.classify('300001')
        assert market == 'CN'
        assert board == 'GEM'

        market, board = SymbolClassifier.classify('301001')
        assert market == 'CN'
        assert board == 'GEM'

    def test_classify_cn_star(self):
        """测试科创板识别"""
        market, board = SymbolClassifier.classify('688001')
        assert market == 'CN'
        assert board == 'STAR'

    def test_classify_cn_bse(self):
        """测试北交所识别"""
        market, board = SymbolClassifier.classify('430001')
        assert market == 'CN'
        assert board == 'BSE'

        market, board = SymbolClassifier.classify('830001')
        assert market == 'CN'
        assert board == 'BSE'

    def test_classify_hk(self):
        """测试港股识别"""
        market, board = SymbolClassifier.classify('00700')
        assert market == 'HK'
        assert board == 'MAIN'

        market, board = SymbolClassifier.classify('00700.HK')
        assert market == 'HK'
        assert board == 'MAIN'

    def test_classify_us(self):
        """测试美股识别"""
        market, board = SymbolClassifier.classify('AAPL')
        assert market == 'US'
        assert board == 'NYSE'

    def test_classify_invalid(self):
        """测试无效代码"""
        with pytest.raises(ValueError):
            SymbolClassifier.classify('INVALID123')

    def test_is_st_stock(self):
        """测试ST股票识别"""
        assert SymbolClassifier.is_st_stock('*ST华电')
        assert SymbolClassifier.is_st_stock('ST华电')
        assert SymbolClassifier.is_st_stock('S*ST华电')
        assert SymbolClassifier.is_st_stock('SST华电')
        assert not SymbolClassifier.is_st_stock('浦发银行')
        assert not SymbolClassifier.is_st_stock('')
        assert not SymbolClassifier.is_st_stock(None)

    def test_detect_board_override_st(self):
        """测试ST板块覆盖"""
        # ST股票应覆盖原板块
        board = SymbolClassifier.detect_board_override(
            symbol='600001',
            stock_name='*ST华电',
            market='CN',
            board='MAIN'
        )
        assert board == 'ST'

        # 非ST股票不覆盖
        board = SymbolClassifier.detect_board_override(
            symbol='600000',
            stock_name='浦发银行',
            market='CN',
            board='MAIN'
        )
        assert board == 'MAIN'

    def test_get_trading_environment_main(self):
        """测试获取主板交易环境"""
        env = SymbolClassifier.get_trading_environment('600000')
        assert env.market == 'CN'
        assert env.board == 'MAIN'
        assert env.channel == 'DIRECT'
        assert str(env) == 'CN_MAIN'

    def test_get_trading_environment_gem(self):
        """测试获取创业板交易环境"""
        env = SymbolClassifier.get_trading_environment('300001')
        assert env.market == 'CN'
        assert env.board == 'GEM'
        assert str(env) == 'CN_GEM'

    def test_get_trading_environment_st(self):
        """测试获取ST股票交易环境"""
        env = SymbolClassifier.get_trading_environment(
            '600001',
            stock_name='*ST华电'
        )
        assert env.market == 'CN'
        assert env.board == 'ST'
        assert str(env) == 'CN_ST'

    def test_get_trading_environment_with_channel(self):
        """测试指定渠道的交易环境"""
        env = SymbolClassifier.get_trading_environment(
            '00700',
            channel='CONNECT'
        )
        assert env.market == 'HK'
        assert env.board == 'MAIN'
        assert env.channel == 'CONNECT'
        assert str(env) == 'HK_MAIN_CONNECT'

    def test_get_board_name(self):
        """测试获取板块中文名"""
        assert SymbolClassifier.get_board_name('MAIN') == '主板'
        assert SymbolClassifier.get_board_name('GEM') == '创业板'
        assert SymbolClassifier.get_board_name('STAR') == '科创板'
        assert SymbolClassifier.get_board_name('BSE') == '北交所'
        assert SymbolClassifier.get_board_name('ST') == 'ST股票'

    def test_get_market_name(self):
        """测试获取市场中文名"""
        assert SymbolClassifier.get_market_name('CN') == '中国A股'
        assert SymbolClassifier.get_market_name('HK') == '香港'
        assert SymbolClassifier.get_market_name('US') == '美国'

    def test_format_symbol_cn(self):
        """测试格式化中国A股代码"""
        # 补齐0
        assert SymbolClassifier.format_symbol('600', 'CN') == '000600'
        # 去除前缀
        assert SymbolClassifier.format_symbol('SH600000', 'CN') == '600000'
        # 已正确格式
        assert SymbolClassifier.format_symbol('600000', 'CN') == '600000'

    def test_format_symbol_hk(self):
        """测试格式化港股代码"""
        # 去除.HK后缀
        assert SymbolClassifier.format_symbol('00700.HK', 'HK') == '00700'
        # 补齐0
        assert SymbolClassifier.format_symbol('700', 'HK') == '00700'

    def test_classify_symbol_convenience_function(self):
        """测试便捷函数"""
        env = classify_symbol('600000')
        assert isinstance(env, TradingEnvironment)
        assert env.market == 'CN'
        assert env.board == 'MAIN'
