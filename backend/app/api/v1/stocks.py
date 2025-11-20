"""Stock-related API endpoints."""

from flask import request
from flask_restful import Resource
from app.services.data_service import DataService
from app.services.indicator_service import IndicatorService


class StockListResource(Resource):
    """Resource for getting list of stocks."""

    def get(self):
        """Get list of all stocks.

        Returns:
            JSON response with stock list
        """
        try:
            stock_list = DataService.get_stock_list()
            # Convert to list of dicts and limit results
            stocks = stock_list.head(100).to_dict('records')

            return {
                'success': True,
                'data': stocks,
                'total': len(stock_list)
            }, 200

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500


class StockSearchResource(Resource):
    """Resource for searching stocks."""

    def get(self):
        """Search stocks by keyword.

        Query params:
            keyword: Search keyword (code or name)

        Returns:
            JSON response with matching stocks
        """
        try:
            keyword = request.args.get('keyword', '')

            if not keyword:
                return {
                    'success': False,
                    'error': 'keyword parameter is required'
                }, 400

            stocks = DataService.search_stock(keyword)

            return {
                'success': True,
                'data': stocks
            }, 200

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500


class StockDataResource(Resource):
    """Resource for getting stock historical data."""

    def get(self, symbol):
        """Get historical K-line data for a stock.

        Args:
            symbol: Stock code

        Query params:
            start_date: Start date (YYYYMMDD format)
            end_date: End date (YYYYMMDD format)
            adjust: Adjustment type (qfq/hfq/none)
            include_indicators: Whether to include technical indicators (true/false)

        Returns:
            JSON response with stock data
        """
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            adjust = request.args.get('adjust', 'qfq')
            include_indicators = request.args.get('include_indicators', 'false').lower() == 'true'

            # Get stock info
            stock_info = DataService.get_stock_info(symbol)

            # Get stock data (with failover)
            df, adapter_used = DataService.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
                use_failover=True
            )

            # Calculate indicators if requested
            if include_indicators:
                df = IndicatorService.calculate_all_indicators(df)

            # Convert to JSON-serializable format
            df['date'] = df['date'].astype(str)
            data = df.to_dict('records')

            response_data = {
                'stock': stock_info,
                'klines': data
            }

            # 添加适配器信息(如果使用了故障转移)
            if adapter_used:
                response_data['data_source'] = adapter_used

            return {
                'success': True,
                'data': response_data
            }, 200

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500
