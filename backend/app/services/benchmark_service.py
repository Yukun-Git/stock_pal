"""
基准指数服务

负责获取基准指数数据，用于回测对比分析。
支持的基准指数：
- CSI300: 沪深300（000300）
- CSI500: 中证500（000905）
- GEM: 创业板指（399006）
- STAR50: 科创50（000688）

注意：指数数据使用 akshare 获取，因为 yfinance 对中国指数历史数据支持较差
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
import akshare as ak

logger = logging.getLogger(__name__)


class BenchmarkService:
    """基准指数数据服务"""

    # 支持的基准指数映射
    BENCHMARK_MAP = {
        'CSI300': {
            'symbol': '沪深300',  # akshare 名称
            'ak_symbol': 'sh000300',  # akshare stock_zh_index_daily 代码
            'yf_symbol': '000300.SS',  # yfinance 格式
            'use_yfinance': True,  # 沪深300用yfinance（数据稳定）
            'name': '沪深300',
            'description': '大盘蓝筹指数'
        },
        'CSI500': {
            'symbol': '中证500',
            'ak_symbol': 'sh000905',
            'yf_symbol': '000905.SS',
            'use_yfinance': False,  # yfinance数据不完整
            'name': '中证500',
            'description': '中盘成长指数'
        },
        'GEM': {
            'symbol': '创业板指',
            'ak_symbol': 'sz399006',
            'yf_symbol': '399006.SZ',
            'use_yfinance': False,
            'name': '创业板指',
            'description': '创业板综合指数'
        },
        'STAR50': {
            'symbol': '科创50',
            'ak_symbol': 'sh000688',
            'yf_symbol': '000688.SS',
            'use_yfinance': False,
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
                'code': value['symbol'],  # 返回给前端显示用
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

        混合数据源策略：
        - 沪深300：使用 yfinance（数据稳定完整）
        - 其他指数：使用 akshare（数据全面但可能不稳定）

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

        benchmark_info = BenchmarkService.BENCHMARK_MAP[benchmark_id]
        use_yfinance = benchmark_info.get('use_yfinance', False)

        try:
            if use_yfinance:
                # 使用 yfinance
                df = BenchmarkService._fetch_via_yfinance(
                    benchmark_id, start_date, end_date
                )
            else:
                # 使用 akshare
                df = BenchmarkService._fetch_via_akshare(
                    benchmark_id, start_date, end_date
                )

            # 缓存结果
            BenchmarkService._cache[cache_key] = df.copy()

            logger.info(f"Benchmark data fetched: {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch benchmark data: {str(e)}")
            raise Exception(f"Failed to fetch benchmark data for {benchmark_id}: {str(e)}")

    @staticmethod
    def _fetch_via_yfinance(
        benchmark_id: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """通过 yfinance 获取基准数据"""
        import yfinance as yf

        yf_symbol = BenchmarkService.BENCHMARK_MAP[benchmark_id]['yf_symbol']
        name = BenchmarkService.BENCHMARK_MAP[benchmark_id]['name']

        logger.info(f"Fetching {name} via yfinance: {yf_symbol}")

        # 转换日期格式
        start = datetime.strptime(start_date, '%Y%m%d').strftime('%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')

        # 获取数据
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(start=start, end=end, auto_adjust=True)

        if df.empty:
            raise Exception(f"No data from yfinance for {yf_symbol}")

        # 标准化格式
        df = df.reset_index()
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        # 确保日期格式
        df['date'] = pd.to_datetime(df['date'])
        if df['date'].dt.tz is not None:
            df['date'] = df['date'].dt.tz_localize(None)

        # 选择需要的列
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('date').reset_index(drop=True)

        return df

    @staticmethod
    def _fetch_via_akshare(
        benchmark_id: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """通过 akshare 获取基准数据

        使用 stock_zh_index_daily API 获取指数全量历史数据，然后过滤日期范围。
        这比 index_zh_a_hist 更稳定可靠。
        """
        ak_symbol = BenchmarkService.BENCHMARK_MAP[benchmark_id]['ak_symbol']
        name = BenchmarkService.BENCHMARK_MAP[benchmark_id]['name']

        logger.info(f"Fetching {name} via akshare: {ak_symbol}")

        try:
            # 使用 stock_zh_index_daily 获取全量数据
            df = ak.stock_zh_index_daily(symbol=ak_symbol)

            if df is None or df.empty:
                raise Exception(f"No data from akshare for {ak_symbol}")

            # 确保日期列为datetime类型
            df['date'] = pd.to_datetime(df['date'])

            # 过滤日期范围
            start_dt = pd.to_datetime(start_date, format='%Y%m%d')
            end_dt = pd.to_datetime(end_date, format='%Y%m%d')
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

            if df.empty:
                raise Exception(f"No data in date range {start_date} to {end_date}")

            # 排序
            df = df.sort_values('date').reset_index(drop=True)

            # 选择需要的列（stock_zh_index_daily已经返回标准列名）
            required_cols = ['date', 'open', 'high', 'low', 'close']
            optional_cols = ['volume']

            for col in required_cols:
                if col not in df.columns:
                    raise Exception(f"Missing required column: {col}")

            for col in optional_cols:
                if col not in df.columns:
                    df[col] = 0  # 某些指数可能没有成交量数据

            df = df[required_cols + optional_cols]

            logger.info(f"Successfully fetched {len(df)} rows for {name}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch {name} data: {str(e)}")
            raise

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
