"""Baostock适配器单元测试."""

import pytest
import pandas as pd
from datetime import datetime

# 导入适配器和异常
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.adapters.baostock_adapter import BaostockAdapter
from app.adapters.exceptions import (
    NetworkException,
    DataNotFoundException,
    UnsupportedMarketException
)


class TestBaostockAdapterProperties:
    """测试适配器基本属性."""

    def setup_method(self):
        """测试前置设置."""
        self.adapter = BaostockAdapter()

    def test_name(self):
        """测试适配器名称."""
        assert self.adapter.name == "baostock"

    def test_display_name(self):
        """测试显示名称."""
        assert "证券宝" in self.adapter.display_name

    def test_supported_markets(self):
        """测试支持的市场."""
        markets = self.adapter.supported_markets
        assert "A-share" in markets
        assert "HK" not in markets
        assert "US" not in markets

    def test_requires_auth(self):
        """测试认证要求."""
        assert self.adapter.requires_auth is False

    def test_timeout(self):
        """测试超时时间."""
        assert self.adapter.timeout == 10

    def test_supports_market_a_share(self):
        """测试支持A股市场."""
        assert self.adapter.supports_market("A-share") is True

    def test_supports_market_hk(self):
        """测试不支持港股市场."""
        assert self.adapter.supports_market("HK") is False

    def test_get_metadata(self):
        """测试获取元数据."""
        metadata = self.adapter.get_metadata()
        assert metadata['name'] == 'baostock'
        assert 'display_name' in metadata
        assert 'supported_markets' in metadata
        assert metadata['requires_auth'] is False


class TestBaostockAdapterConversion:
    """测试代码转换功能."""

    def setup_method(self):
        """测试前置设置."""
        self.adapter = BaostockAdapter()

    def test_convert_symbol_shanghai(self):
        """测试上海股票代码转换."""
        result = self.adapter._convert_symbol_format('600519')
        assert result == 'sh.600519'

    def test_convert_symbol_shenzhen(self):
        """测试深圳股票代码转换."""
        result = self.adapter._convert_symbol_format('000001')
        assert result == 'sz.000001'

    def test_convert_symbol_chuangye(self):
        """测试创业板股票代码转换."""
        result = self.adapter._convert_symbol_format('300001')
        assert result == 'sz.300001'

    def test_convert_date_format(self):
        """测试日期格式转换."""
        result = self.adapter._convert_date_format('20230101')
        assert result == '2023-01-01'

    def test_convert_date_format_already_formatted(self):
        """测试已格式化的日期."""
        result = self.adapter._convert_date_format('2023-01-01')
        assert result == '2023-01-01'


class TestBaostockAdapterGetStockData:
    """测试获取股票数据功能."""

    def setup_method(self):
        """测试前置设置."""
        self.adapter = BaostockAdapter()

    def test_get_stock_data_success(self):
        """测试成功获取股票数据."""
        # 获取平安银行2023年第一季度数据
        df = self.adapter.get_stock_data(
            symbol='000001',
            start_date='20230101',
            end_date='20230331'
        )

        # 验证返回的DataFrame
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        # 验证必要的列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

        # 验证数据类型
        assert df['close'].dtype in ['float64', 'float32']
        assert df['volume'].dtype in ['float64', 'int64', 'float32']

        # 验证索引是日期类型
        assert isinstance(df.index, pd.DatetimeIndex)

        # 验证数据排序（升序）
        assert df.index.is_monotonic_increasing

    def test_get_stock_data_shanghai(self):
        """测试获取上海股票数据."""
        df = self.adapter.get_stock_data(
            symbol='600519',  # 贵州茅台
            start_date='20231201',
            end_date='20231231'
        )

        assert df is not None
        assert len(df) > 0

    def test_get_stock_data_unsupported_market(self):
        """测试获取港股数据抛出异常."""
        with pytest.raises(UnsupportedMarketException) as exc_info:
            self.adapter.get_stock_data(
                symbol='00700.HK',
                start_date='20230101',
                end_date='20230331'
            )

        assert 'HK' in str(exc_info.value)

    def test_get_stock_data_with_adjust(self):
        """测试不同复权类型."""
        # 前复权
        df_qfq = self.adapter.get_stock_data(
            symbol='000001',
            start_date='20231201',
            end_date='20231231',
            adjust='qfq'
        )
        assert len(df_qfq) > 0

        # 后复权
        df_hfq = self.adapter.get_stock_data(
            symbol='000001',
            start_date='20231201',
            end_date='20231231',
            adjust='hfq'
        )
        assert len(df_hfq) > 0


class TestBaostockAdapterSearchStock:
    """测试搜索股票功能."""

    def setup_method(self):
        """测试前置设置."""
        self.adapter = BaostockAdapter()

    def test_search_stock_by_code(self):
        """测试按代码搜索."""
        results = self.adapter.search_stock('000001')

        assert results is not None
        assert isinstance(results, list)
        assert len(results) > 0

        # 验证返回格式
        first_result = results[0]
        assert 'code' in first_result
        assert 'name' in first_result
        assert 'market' in first_result
        assert first_result['market'] == 'A-share'

    def test_search_stock_by_name(self):
        """测试按名称搜索."""
        results = self.adapter.search_stock('平安')

        assert results is not None
        assert len(results) > 0

        # 应该找到平安银行
        codes = [r['code'] for r in results]
        # 验证至少有搜索结果
        assert len(codes) > 0

    def test_search_stock_empty_result(self):
        """测试搜索无结果."""
        results = self.adapter.search_stock('XXXXXXXX不存在的股票')

        assert results is not None
        assert isinstance(results, list)
        assert len(results) == 0


class TestBaostockAdapterGetStockInfo:
    """测试获取股票信息功能."""

    def setup_method(self):
        """测试前置设置."""
        self.adapter = BaostockAdapter()

    def test_get_stock_info_success(self):
        """测试成功获取股票信息."""
        info = self.adapter.get_stock_info('000001')

        assert info is not None
        assert isinstance(info, dict)
        assert 'code' in info
        assert 'name' in info
        assert 'market' in info
        assert info['code'] == '000001'
        assert info['market'] == 'A-share'

    def test_get_stock_info_unknown(self):
        """测试获取未知股票信息."""
        info = self.adapter.get_stock_info('999999')

        # 应该返回默认信息而不是抛异常
        assert info is not None
        assert 'code' in info
        assert 'name' in info


class TestBaostockAdapterHealthCheck:
    """测试健康检查功能."""

    def setup_method(self):
        """测试前置设置."""
        self.adapter = BaostockAdapter()

    def test_health_check(self):
        """测试健康检查."""
        result = self.adapter.health_check()

        assert result is not None
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'response_time_ms' in result
        assert 'message' in result
        assert 'checked_at' in result

        # 应该是在线状态
        assert result['status'] == 'online'
        assert result['response_time_ms'] > 0


class TestBaostockAdapterValidateConfig:
    """测试配置验证功能."""

    def setup_method(self):
        """测试前置设置."""
        self.adapter = BaostockAdapter()

    def test_validate_config(self):
        """测试配置验证."""
        # Baostock不需要认证，应该总是返回True
        assert self.adapter.validate_config() is True


# 集成测试（需要网络）
class TestBaostockAdapterIntegration:
    """集成测试（需要网络连接）."""

    def setup_method(self):
        """测试前置设置."""
        self.adapter = BaostockAdapter()

    @pytest.mark.slow
    def test_full_workflow(self):
        """测试完整工作流程."""
        # 1. 搜索股票
        results = self.adapter.search_stock('平安')
        assert len(results) > 0

        # 2. 获取股票信息
        stock_code = results[0]['code']
        info = self.adapter.get_stock_info(stock_code)
        assert info['code'] == stock_code

        # 3. 获取股票数据
        df = self.adapter.get_stock_data(
            symbol=stock_code,
            start_date='20231201',
            end_date='20231231'
        )
        assert len(df) > 0

        # 4. 健康检查
        health = self.adapter.health_check()
        assert health['status'] == 'online'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
