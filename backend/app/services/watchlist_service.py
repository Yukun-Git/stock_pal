"""Watchlist service for managing user's stock watchlists."""

from typing import Optional, Dict, List
from app.utils.db import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class WatchlistService:
    """Service for handling user watchlist operations."""

    @staticmethod
    def get_user_watchlist(
        user_id: str,
        group_id: Optional[int] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> List[Dict]:
        """
        Get user's watchlist stocks with group information.

        Args:
            user_id: User ID (UUID)
            group_id: Filter by group ID (optional)
            sort_by: Sort field (code, name, created_at)
            sort_order: Sort order (asc, desc)

        Returns:
            List of stock dicts with group information
        """
        try:
            # Validate sort parameters
            valid_sort_fields = {'code': 'stock_code', 'name': 'stock_name', 'created_at': 'ws.created_at'}
            sort_field = valid_sort_fields.get(sort_by, 'ws.created_at')
            sort_direction = 'ASC' if sort_order.lower() == 'asc' else 'DESC'

            # Build query
            query = f"""
                SELECT
                    ws.id,
                    ws.stock_code,
                    ws.stock_name,
                    ws.note,
                    ws.group_id,
                    ws.created_at,
                    ws.updated_at,
                    wg.name as group_name,
                    wg.color as group_color
                FROM watchlist_stocks ws
                LEFT JOIN watchlist_groups wg ON ws.group_id = wg.id
                WHERE ws.user_id = %s
            """

            params = [user_id]

            # Add group filter if specified
            if group_id is not None:
                query += " AND ws.group_id = %s"
                params.append(group_id)

            # Add sorting
            query += f" ORDER BY {sort_field} {sort_direction}"

            results = DatabaseManager.execute_query(query, tuple(params), fetch=True)
            return [dict(row) for row in results] if results else []

        except Exception as e:
            logger.error(f"Error fetching watchlist for user {user_id}: {e}")
            raise

    @staticmethod
    def add_stock(
        user_id: str,
        stock_code: str,
        stock_name: str,
        group_id: Optional[int] = None,
        note: Optional[str] = None
    ) -> Dict:
        """
        Add a stock to user's watchlist.

        Args:
            user_id: User ID (UUID)
            stock_code: Stock code (6-digit)
            stock_name: Stock name
            group_id: Group ID (optional)
            note: User note (optional)

        Returns:
            Created stock record dict

        Raises:
            ValueError: If stock already exists or validation fails
            Exception: For database errors
        """
        try:
            # Validate stock code format
            if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
                raise ValueError("股票代码必须为6位数字")

            if not stock_name or not stock_name.strip():
                raise ValueError("股票名称不能为空")

            # Check if stock already exists
            check_query = """
                SELECT id FROM watchlist_stocks
                WHERE user_id = %s AND stock_code = %s
            """
            existing = DatabaseManager.execute_query(
                check_query,
                (user_id, stock_code),
                fetch=True
            )

            if existing and len(existing) > 0:
                raise ValueError("该股票已在自选股中")

            # If group_id is provided, verify it belongs to the user
            if group_id is not None:
                group_check_query = """
                    SELECT id FROM watchlist_groups
                    WHERE id = %s AND user_id = %s
                """
                group_exists = DatabaseManager.execute_query(
                    group_check_query,
                    (group_id, user_id),
                    fetch=True
                )
                if not group_exists:
                    raise ValueError("指定的分组不存在或不属于当前用户")

            # Insert stock
            insert_query = """
                INSERT INTO watchlist_stocks (user_id, stock_code, stock_name, group_id, note)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, stock_code, stock_name, group_id, note, created_at, updated_at
            """
            results = DatabaseManager.execute_query(
                insert_query,
                (user_id, stock_code, stock_name, group_id, note),
                fetch=True
            )

            if results and len(results) > 0:
                return dict(results[0])
            else:
                raise Exception("添加自选股失败")

        except ValueError as e:
            logger.warning(f"Validation error adding stock {stock_code}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error adding stock {stock_code} for user {user_id}: {e}")
            raise

    @staticmethod
    def delete_stock(user_id: str, stock_id: int) -> bool:
        """
        Delete a stock from user's watchlist.

        Args:
            user_id: User ID (UUID)
            stock_id: Stock record ID

        Returns:
            True if deleted successfully, False if not found

        Raises:
            Exception: For database errors
        """
        try:
            # Delete only if belongs to user (for security)
            delete_query = """
                DELETE FROM watchlist_stocks
                WHERE id = %s AND user_id = %s
            """
            DatabaseManager.execute_query(delete_query, (stock_id, user_id), fetch=False)

            # Check if row was actually deleted
            check_query = """
                SELECT id FROM watchlist_stocks
                WHERE id = %s
            """
            remaining = DatabaseManager.execute_query(check_query, (stock_id,), fetch=True)

            return not remaining or len(remaining) == 0

        except Exception as e:
            logger.error(f"Error deleting stock {stock_id} for user {user_id}: {e}")
            raise

    @staticmethod
    def update_stock(user_id: str, stock_id: int, updates: Dict) -> Dict:
        """
        Update a stock in user's watchlist.

        Args:
            user_id: User ID (UUID)
            stock_id: Stock record ID
            updates: Dict with fields to update (group_id, note)

        Returns:
            Updated stock record dict

        Raises:
            ValueError: If validation fails or stock not found
            Exception: For database errors
        """
        try:
            # Verify stock belongs to user
            check_query = """
                SELECT id FROM watchlist_stocks
                WHERE id = %s AND user_id = %s
            """
            existing = DatabaseManager.execute_query(
                check_query,
                (stock_id, user_id),
                fetch=True
            )

            if not existing or len(existing) == 0:
                raise ValueError("记录不存在或不属于当前用户")

            # Build update query dynamically
            allowed_fields = {'group_id', 'note'}
            update_fields = []
            params = []

            for field, value in updates.items():
                if field in allowed_fields:
                    # Special handling for group_id validation
                    if field == 'group_id' and value is not None:
                        group_check_query = """
                            SELECT id FROM watchlist_groups
                            WHERE id = %s AND user_id = %s
                        """
                        group_exists = DatabaseManager.execute_query(
                            group_check_query,
                            (value, user_id),
                            fetch=True
                        )
                        if not group_exists:
                            raise ValueError("指定的分组不存在或不属于当前用户")

                    update_fields.append(f"{field} = %s")
                    params.append(value)

            if not update_fields:
                raise ValueError("没有可更新的字段")

            # Add stock_id and user_id to params
            params.extend([stock_id, user_id])

            # Execute update
            update_query = f"""
                UPDATE watchlist_stocks
                SET {', '.join(update_fields)}
                WHERE id = %s AND user_id = %s
                RETURNING id, stock_code, stock_name, group_id, note, created_at, updated_at
            """
            results = DatabaseManager.execute_query(update_query, tuple(params), fetch=True)

            if results and len(results) > 0:
                return dict(results[0])
            else:
                raise Exception("更新失败")

        except ValueError as e:
            logger.warning(f"Validation error updating stock {stock_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating stock {stock_id} for user {user_id}: {e}")
            raise

    @staticmethod
    def batch_delete_stocks(user_id: str, stock_ids: List[int]) -> int:
        """
        Delete multiple stocks from user's watchlist.

        Args:
            user_id: User ID (UUID)
            stock_ids: List of stock record IDs

        Returns:
            Number of stocks deleted

        Raises:
            ValueError: If stock_ids is empty or too large
            Exception: For database errors
        """
        try:
            if not stock_ids:
                raise ValueError("股票ID列表不能为空")

            if len(stock_ids) > 50:
                raise ValueError("批量删除最多支持50只股票")

            # Use ANY operator for batch delete
            delete_query = """
                DELETE FROM watchlist_stocks
                WHERE id = ANY(%s) AND user_id = %s
            """
            DatabaseManager.execute_query(delete_query, (stock_ids, user_id), fetch=False)

            # Count how many were actually deleted
            check_query = """
                SELECT COUNT(*) as count
                FROM watchlist_stocks
                WHERE id = ANY(%s)
            """
            remaining = DatabaseManager.execute_query(check_query, (stock_ids,), fetch=True)

            deleted_count = len(stock_ids) - (remaining[0]['count'] if remaining else 0)
            return deleted_count

        except ValueError as e:
            logger.warning(f"Validation error batch deleting stocks: {e}")
            raise
        except Exception as e:
            logger.error(f"Error batch deleting stocks for user {user_id}: {e}")
            raise

    @staticmethod
    def check_stock_in_watchlist(user_id: str, stock_code: str) -> Optional[Dict]:
        """
        Check if a stock is in user's watchlist.

        Args:
            user_id: User ID (UUID)
            stock_code: Stock code (6-digit)

        Returns:
            Dict with watchlist info if exists, None otherwise
        """
        try:
            query = """
                SELECT
                    ws.id as watchlist_id,
                    ws.group_id,
                    wg.name as group_name
                FROM watchlist_stocks ws
                LEFT JOIN watchlist_groups wg ON ws.group_id = wg.id
                WHERE ws.user_id = %s AND ws.stock_code = %s
                LIMIT 1
            """
            results = DatabaseManager.execute_query(query, (user_id, stock_code), fetch=True)

            if results and len(results) > 0:
                row = dict(results[0])
                return {
                    'in_watchlist': True,
                    'watchlist_id': row['watchlist_id'],
                    'group_name': row['group_name']
                }
            return {'in_watchlist': False}

        except Exception as e:
            logger.error(f"Error checking stock {stock_code} for user {user_id}: {e}")
            raise
