"""Watchlist API endpoints."""

from flask import request
from flask_restful import Resource
from app.services.watchlist_service import WatchlistService
from app.services.watchlist_group_service import WatchlistGroupService
from app.utils.auth import jwt_required_resource
from app.utils.response import convert_to_json_serializable
import logging

logger = logging.getLogger(__name__)


class WatchlistResource(Resource):
    """Resource for watchlist operations."""

    @jwt_required_resource
    def get(self, current_user):
        """
        Get user's watchlist.

        Query params:
            group_id (optional): Filter by group ID
            sort_by (optional): Sort field (code, name, created_at), default: created_at
            sort_order (optional): Sort order (asc, desc), default: desc
            include_quotes (optional): Whether to include real-time quotes (true/false), default: false

        Returns:
            200: Success with watchlist data
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']

            # Parse query parameters
            group_id = request.args.get('group_id', type=int)
            sort_by = request.args.get('sort_by', 'created_at')
            sort_order = request.args.get('sort_order', 'desc')
            include_quotes = request.args.get('include_quotes', 'false').lower() == 'true'

            # Get watchlist
            stocks = WatchlistService.get_user_watchlist(
                user_id=user_id,
                group_id=group_id,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # TODO: Add real-time quotes if requested (Phase 3)
            if include_quotes:
                logger.info("Real-time quotes not yet implemented (Phase 3)")

            return {
                'status': 'success',
                'data': {
                    'stocks': convert_to_json_serializable(stocks),
                    'total': len(stocks)
                }
            }, 200

        except Exception as e:
            logger.error(f"Error getting watchlist for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '获取自选股列表失败',
                'code': 'WATCHLIST_FETCH_ERROR'
            }, 500

    @jwt_required_resource
    def post(self, current_user):
        """
        Add a stock to watchlist.

        Request body:
            {
                "stock_code": "600000",
                "stock_name": "浦发银行",
                "group_id": 5 (optional),
                "note": "关注技术突破" (optional)
            }

        Returns:
            201: Stock added successfully
            400: Validation error
            409: Stock already exists
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']
            data = request.get_json()

            if not data:
                return {
                    'status': 'error',
                    'error': '请求体不能为空',
                    'code': 'INVALID_REQUEST'
                }, 400

            # Validate required fields
            stock_code = data.get('stock_code')
            stock_name = data.get('stock_name')

            if not stock_code or not stock_name:
                return {
                    'status': 'error',
                    'error': '股票代码和名称不能为空',
                    'code': 'MISSING_REQUIRED_FIELDS'
                }, 400

            # Optional fields
            group_id = data.get('group_id')
            note = data.get('note')

            # Add stock
            result = WatchlistService.add_stock(
                user_id=user_id,
                stock_code=stock_code,
                stock_name=stock_name,
                group_id=group_id,
                note=note
            )

            return {
                'status': 'success',
                'data': convert_to_json_serializable(result),
                'message': '自选股添加成功'
            }, 201

        except ValueError as e:
            # Validation errors
            error_msg = str(e)
            if '已在自选股中' in error_msg:
                code = 'STOCK_ALREADY_EXISTS'
                status_code = 409
            elif '股票代码' in error_msg:
                code = 'INVALID_STOCK_CODE'
                status_code = 400
            elif '不属于当前用户' in error_msg or '不存在' in error_msg:
                code = 'GROUP_NOT_FOUND'
                status_code = 400
            else:
                code = 'VALIDATION_ERROR'
                status_code = 400

            return {
                'status': 'error',
                'error': error_msg,
                'code': code
            }, status_code

        except Exception as e:
            logger.error(f"Error adding stock for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '添加自选股失败',
                'code': 'ADD_STOCK_ERROR'
            }, 500


class WatchlistItemResource(Resource):
    """Resource for individual watchlist item operations."""

    @jwt_required_resource
    def put(self, current_user, stock_id):
        """
        Update a watchlist item.

        Args:
            stock_id: Watchlist stock ID

        Request body:
            {
                "group_id": 6 (optional),
                "note": "已突破" (optional)
            }

        Returns:
            200: Update successful
            400: Validation error
            404: Stock not found
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']
            data = request.get_json()

            if not data:
                return {
                    'status': 'error',
                    'error': '请求体不能为空',
                    'code': 'INVALID_REQUEST'
                }, 400

            # Update stock
            result = WatchlistService.update_stock(
                user_id=user_id,
                stock_id=stock_id,
                updates=data
            )

            return {
                'status': 'success',
                'data': convert_to_json_serializable(result),
                'message': '更新成功'
            }, 200

        except ValueError as e:
            error_msg = str(e)
            if '不存在' in error_msg or '不属于' in error_msg:
                code = 'NOT_FOUND'
                status_code = 404
            else:
                code = 'VALIDATION_ERROR'
                status_code = 400

            return {
                'status': 'error',
                'error': error_msg,
                'code': code
            }, status_code

        except Exception as e:
            logger.error(f"Error updating stock {stock_id} for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '更新失败',
                'code': 'UPDATE_ERROR'
            }, 500

    @jwt_required_resource
    def delete(self, current_user, stock_id):
        """
        Delete a watchlist item.

        Args:
            stock_id: Watchlist stock ID

        Returns:
            200: Delete successful
            404: Stock not found
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']

            # Delete stock
            success = WatchlistService.delete_stock(user_id, stock_id)

            if not success:
                return {
                    'status': 'error',
                    'error': '记录不存在或不属于当前用户',
                    'code': 'NOT_FOUND'
                }, 404

            return {
                'status': 'success',
                'message': '删除成功'
            }, 200

        except Exception as e:
            logger.error(f"Error deleting stock {stock_id} for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '删除失败',
                'code': 'DELETE_ERROR'
            }, 500


class WatchlistBatchResource(Resource):
    """Resource for batch watchlist operations."""

    @jwt_required_resource
    def delete(self, current_user):
        """
        Batch delete watchlist items.

        Request body:
            {
                "ids": [123, 124, 125]
            }

        Returns:
            200: Batch delete successful
            400: Validation error
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']
            data = request.get_json()

            if not data:
                return {
                    'status': 'error',
                    'error': '请求体不能为空',
                    'code': 'INVALID_REQUEST'
                }, 400

            ids = data.get('ids')

            if not ids or not isinstance(ids, list):
                return {
                    'status': 'error',
                    'error': 'ids字段必须是数组',
                    'code': 'INVALID_IDS_FORMAT'
                }, 400

            # Batch delete
            deleted_count = WatchlistService.batch_delete_stocks(user_id, ids)

            return {
                'status': 'success',
                'data': {
                    'deleted_count': deleted_count
                },
                'message': '批量删除成功'
            }, 200

        except ValueError as e:
            return {
                'status': 'error',
                'error': str(e),
                'code': 'VALIDATION_ERROR'
            }, 400

        except Exception as e:
            logger.error(f"Error batch deleting stocks for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '批量删除失败',
                'code': 'BATCH_DELETE_ERROR'
            }, 500

    @jwt_required_resource
    def post(self, current_user):
        """
        Batch import watchlist items.

        Request body:
            {
                "stocks": [
                    {"stock_code": "600000", "stock_name": "浦发银行"},
                    {"stock_code": "000001", "stock_name": "平安银行"}
                ],
                "group_id": 5 (optional),
                "skip_duplicates": true (optional, default: true)
            }

        Returns:
            200: Import completed
            400: Validation error
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']
            data = request.get_json()

            if not data:
                return {
                    'status': 'error',
                    'error': '请求体不能为空',
                    'code': 'INVALID_REQUEST'
                }, 400

            stocks = data.get('stocks')

            if not stocks or not isinstance(stocks, list):
                return {
                    'status': 'error',
                    'error': 'stocks字段必须是数组',
                    'code': 'INVALID_STOCKS_FORMAT'
                }, 400

            if len(stocks) > 100:
                return {
                    'status': 'error',
                    'error': '批量导入最多支持100只股票',
                    'code': 'TOO_MANY_STOCKS'
                }, 400

            group_id = data.get('group_id')
            skip_duplicates = data.get('skip_duplicates', True)

            imported_count = 0
            skipped_count = 0
            failed = []

            # Import each stock
            for stock in stocks:
                stock_code = stock.get('stock_code')
                stock_name = stock.get('stock_name')

                if not stock_code or not stock_name:
                    failed.append({
                        'stock': stock,
                        'reason': '股票代码或名称为空'
                    })
                    continue

                try:
                    WatchlistService.add_stock(
                        user_id=user_id,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        group_id=group_id
                    )
                    imported_count += 1
                except ValueError as e:
                    if skip_duplicates and '已在自选股中' in str(e):
                        skipped_count += 1
                    else:
                        failed.append({
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'reason': str(e)
                        })

            return {
                'status': 'success',
                'data': {
                    'imported_count': imported_count,
                    'skipped_count': skipped_count,
                    'failed': failed
                },
                'message': '导入完成'
            }, 200

        except Exception as e:
            logger.error(f"Error importing stocks for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '导入失败',
                'code': 'IMPORT_ERROR'
            }, 500


class WatchlistCheckResource(Resource):
    """Resource for checking if a stock is in watchlist."""

    @jwt_required_resource
    def get(self, current_user, stock_code):
        """
        Check if a stock is in user's watchlist.

        Args:
            stock_code: Stock code (6-digit)

        Returns:
            200: Check result
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']

            # Check stock
            result = WatchlistService.check_stock_in_watchlist(user_id, stock_code)

            return {
                'status': 'success',
                'data': result
            }, 200

        except Exception as e:
            logger.error(f"Error checking stock {stock_code} for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '检查失败',
                'code': 'CHECK_ERROR'
            }, 500
