"""
基准指数服务

负责获取基准指数数据，用于回测对比分析。
支持的基准指数：
- CSI300: 沪深300（000300）
- CSI500: 中证500（000905）
- GEM: 创业板指（399006）
- STAR50: 科创50（000688）
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class BenchmarkService:
    """基准指数数据服务"""

    # 支持的基准指数映射
    BENCHMARK_MAP = {
        'CSI300': {
            'code': '000300',
            'em_symbol': 'sh000300',  # 东方财富接口需要的格式
            'name': '沪深300',
            'description': '大盘蓝筹指数'
        },
        'CSI500': {
            'code': '000905',
            'em_symbol': 'sh000905',
            'name': '中证500',
            'description': '中盘成长指数'
        },
        'GEM': {
            'code': '399006',
            'em_symbol': 'sz399006',
            'name': '创业板指',
            'description': '创业板综合指数'
        },
        'STAR50': {
            'code': '000688',
            'em_symbol': 'sh000688',
            'name': '科创50',
            'description': '科创板龙头指数'
        }
    }

    # 简单内存缓存（生产环境应使用Redis等）
    _cache: Dict[str, pd.DataFrame] = {}

    @staticmethod
    def get_benchmark_list() -> list:
        """
        获取支持的基准指数列表

        Returns:
            list: 基准指数列表
        """
        return [
            {
                'id': key,
                'code': value['code'],
                'name': value['name'],
                'description': value['description']
            }
            for key, value in BenchmarkService.BENCHMARK_MAP.items()
        ]

    @staticmethod
    def get_benchmark_data(
        benchmark_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取基准指数历史数据

        Args:
            benchmark_id: 基准指数ID（如'CSI300'）
            start_date: 开始日期，格式'YYYYMMDD'
            end_date: 结束日期，格式'YYYYMMDD'

        Returns:
            DataFrame: 包含列 [date, open, high, low, close, volume]

        Raises:
            ValueError: 如果benchmark_id不支持
            Exception: 数据获取失败
        """
        # 验证基准ID
        if benchmark_id not in BenchmarkService.BENCHMARK_MAP:
            raise ValueError(
                f"Unsupported benchmark: {benchmark_id}. "
                f"Supported: {list(BenchmarkService.BENCHMARK_MAP.keys())}"
            )

        # 获取指数代码（东方财富格式）
        em_symbol = BenchmarkService.BENCHMARK_MAP[benchmark_id]['em_symbol']

        # 默认日期范围
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')

        # 检查缓存
        cache_key = f"{benchmark_id}_{start_date}_{end_date}"
        if cache_key in BenchmarkService._cache:
            logger.debug(f"Benchmark cache hit: {cache_key}")
            return BenchmarkService._cache[cache_key].copy()

        try:
            # 从AkShare获取指数数据 (使用东方财富接口)
            logger.info(f"Fetching benchmark data: {benchmark_id} ({em_symbol}), {start_date} - {end_date}")

            df = ak.stock_zh_index_daily_em(symbol=em_symbol)

            if df.empty:
                raise Exception(f"No data found for benchmark {benchmark_id}")

            # 确保列名正确（stock_zh_index_daily_em返回的列已经是标准格式）
            # 列：date, open, close, high, low, volume, amount

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])

            # 筛选日期范围
            start_dt = pd.to_datetime(start_date, format='%Y%m%d')
            end_dt = pd.to_datetime(end_date, format='%Y%m%d')
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

            # 排序
            df = df.sort_values('date').reset_index(drop=True)

            # 选择需要的列
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

            if df.empty:
                raise Exception(f"No data in date range for benchmark {benchmark_id}")

            # 缓存结果
            BenchmarkService._cache[cache_key] = df.copy()

            logger.info(f"Benchmark data fetched: {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch benchmark data: {str(e)}")
            raise Exception(f"Failed to fetch benchmark data for {benchmark_id}: {str(e)}")

    @staticmethod
    def calculate_benchmark_returns(
        benchmark_data: pd.DataFrame,
        initial_capital: float = 100000
    ) -> pd.Series:
        """
        计算基准指数的日收益率

        Args:
            benchmark_data: 基准数据（包含close列）
            initial_capital: 初始资金（用于计算权益曲线）

        Returns:
            pd.Series: 日收益率序列（index为日期）
        """
        if 'close' not in benchmark_data.columns:
            raise ValueError("benchmark_data must contain 'close' column")

        # 计算日收益率
        returns = benchmark_data.set_index('date')['close'].pct_change().dropna()
        return returns

    @staticmethod
    def calculate_benchmark_equity(
        benchmark_data: pd.DataFrame,
        initial_capital: float = 100000
    ) -> pd.DataFrame:
        """
        计算基准指数的权益曲线（归一化到初始资金）

        Args:
            benchmark_data: 基准数据（包含close列）
            initial_capital: 初始资金

        Returns:
            pd.DataFrame: 包含列 [date, equity]
        """
        if 'close' not in benchmark_data.columns:
            raise ValueError("benchmark_data must contain 'close' column")

        # 计算归一化的权益曲线
        # 基准权益 = 初始资金 * (当前价格 / 起始价格)
        df = benchmark_data.copy()
        initial_price = df['close'].iloc[0]
        df['equity'] = initial_capital * (df['close'] / initial_price)

        return df[['date', 'equity']]

    @staticmethod
    def align_dates(
        strategy_dates: pd.Series,
        benchmark_dates: pd.Series
    ) -> tuple:
        """
        对齐策略和基准的日期（取交集）

        Args:
            strategy_dates: 策略日期序列
            benchmark_dates: 基准日期序列

        Returns:
            tuple: (aligned_strategy_dates, aligned_benchmark_dates)
        """
        # 转换为日期类型
        strategy_dates = pd.to_datetime(strategy_dates)
        benchmark_dates = pd.to_datetime(benchmark_dates)

        # 找到共同的日期
        common_dates = strategy_dates[strategy_dates.isin(benchmark_dates)]

        return common_dates, common_dates

    @staticmethod
    def clear_cache():
        """清空缓存"""
        BenchmarkService._cache.clear()
        logger.info("Benchmark cache cleared")
