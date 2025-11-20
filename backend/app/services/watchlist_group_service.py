"""Watchlist group service for managing user's stock groups."""

from typing import Optional, Dict, List
from app.utils.db import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class WatchlistGroupService:
    """Service for handling watchlist group operations."""

    @staticmethod
    def get_user_groups(user_id: str, include_counts: bool = False) -> List[Dict]:
        """
        Get user's watchlist groups.

        Args:
            user_id: User ID (UUID)
            include_counts: Whether to include stock count for each group

        Returns:
            List of group dicts
        """
        try:
            if include_counts:
                query = """
                    SELECT
                        wg.id,
                        wg.name,
                        wg.color,
                        wg.sort_order,
                        wg.created_at,
                        wg.updated_at,
                        COUNT(ws.id) as stock_count
                    FROM watchlist_groups wg
                    LEFT JOIN watchlist_stocks ws ON wg.id = ws.group_id
                    WHERE wg.user_id = %s
                    GROUP BY wg.id, wg.name, wg.color, wg.sort_order, wg.created_at, wg.updated_at
                    ORDER BY wg.sort_order, wg.id
                """
            else:
                query = """
                    SELECT
                        id,
                        name,
                        color,
                        sort_order,
                        created_at,
                        updated_at
                    FROM watchlist_groups
                    WHERE user_id = %s
                    ORDER BY sort_order, id
                """

            results = DatabaseManager.execute_query(query, (user_id,), fetch=True)
            return [dict(row) for row in results] if results else []

        except Exception as e:
            logger.error(f"Error fetching groups for user {user_id}: {e}")
            raise

    @staticmethod
    def create_group(
        user_id: str,
        name: str,
        color: Optional[str] = None,
        sort_order: Optional[int] = None
    ) -> Dict:
        """
        Create a new watchlist group.

        Args:
            user_id: User ID (UUID)
            name: Group name
            color: Color tag (optional)
            sort_order: Sort order (optional, defaults to max+1)

        Returns:
            Created group dict

        Raises:
            ValueError: If validation fails
            Exception: For database errors
        """
        try:
            # Validate name
            if not name or not name.strip():
                raise ValueError("分组名称不能为空")

            if len(name) > 50:
                raise ValueError("分组名称最长50个字符")

            # Check for duplicate name
            check_query = """
                SELECT id FROM watchlist_groups
                WHERE user_id = %s AND name = %s
            """
            existing = DatabaseManager.execute_query(
                check_query,
                (user_id, name),
                fetch=True
            )

            if existing and len(existing) > 0:
                raise ValueError("分组名称已存在")

            # If sort_order not provided, use max + 1
            if sort_order is None:
                max_query = """
                    SELECT COALESCE(MAX(sort_order), 0) + 1 as next_order
                    FROM watchlist_groups
                    WHERE user_id = %s
                """
                max_result = DatabaseManager.execute_query(max_query, (user_id,), fetch=True)
                sort_order = max_result[0]['next_order'] if max_result else 1

            # Insert group
            insert_query = """
                INSERT INTO watchlist_groups (user_id, name, color, sort_order)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, color, sort_order, created_at, updated_at
            """
            results = DatabaseManager.execute_query(
                insert_query,
                (user_id, name, color, sort_order),
                fetch=True
            )

            if results and len(results) > 0:
                return dict(results[0])
            else:
                raise Exception("创建分组失败")

        except ValueError as e:
            logger.warning(f"Validation error creating group '{name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating group '{name}' for user {user_id}: {e}")
            raise

    @staticmethod
    def update_group(
        user_id: str,
        group_id: int,
        updates: Dict
    ) -> Dict:
        """
        Update a watchlist group.

        Args:
            user_id: User ID (UUID)
            group_id: Group ID
            updates: Dict with fields to update (name, color, sort_order)

        Returns:
            Updated group dict

        Raises:
            ValueError: If validation fails or group not found
            Exception: For database errors
        """
        try:
            # Verify group belongs to user
            check_query = """
                SELECT id, name FROM watchlist_groups
                WHERE id = %s AND user_id = %s
            """
            existing = DatabaseManager.execute_query(
                check_query,
                (group_id, user_id),
                fetch=True
            )

            if not existing or len(existing) == 0:
                raise ValueError("分组不存在或不属于当前用户")

            # Check if it's the default group
            if existing[0]['name'] == '未分类':
                # Default group can only update color and sort_order, not name
                if 'name' in updates and updates['name'] != '未分类':
                    raise ValueError("不能修改默认分组的名称")

            # Build update query dynamically
            allowed_fields = {'name', 'color', 'sort_order'}
            update_fields = []
            params = []

            for field, value in updates.items():
                if field in allowed_fields:
                    # Validate name if updating
                    if field == 'name':
                        if not value or not value.strip():
                            raise ValueError("分组名称不能为空")
                        if len(value) > 50:
                            raise ValueError("分组名称最长50个字符")

                        # Check for duplicate name (excluding current group)
                        dup_query = """
                            SELECT id FROM watchlist_groups
                            WHERE user_id = %s AND name = %s AND id != %s
                        """
                        dup_result = DatabaseManager.execute_query(
                            dup_query,
                            (user_id, value, group_id),
                            fetch=True
                        )
                        if dup_result and len(dup_result) > 0:
                            raise ValueError("分组名称已存在")

                    # Validate sort_order if updating
                    if field == 'sort_order' and value is not None:
                        if value < 0:
                            raise ValueError("排序顺序不能为负数")

                    update_fields.append(f"{field} = %s")
                    params.append(value)

            if not update_fields:
                raise ValueError("没有可更新的字段")

            # Add group_id and user_id to params
            params.extend([group_id, user_id])

            # Execute update
            update_query = f"""
                UPDATE watchlist_groups
                SET {', '.join(update_fields)}
                WHERE id = %s AND user_id = %s
                RETURNING id, name, color, sort_order, created_at, updated_at
            """
            results = DatabaseManager.execute_query(update_query, tuple(params), fetch=True)

            if results and len(results) > 0:
                return dict(results[0])
            else:
                raise Exception("更新失败")

        except ValueError as e:
            logger.warning(f"Validation error updating group {group_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating group {group_id} for user {user_id}: {e}")
            raise

    @staticmethod
    def delete_group(user_id: str, group_id: int) -> bool:
        """
        Delete a watchlist group.

        Args:
            user_id: User ID (UUID)
            group_id: Group ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If trying to delete default group or group not found
            Exception: For database errors
        """
        try:
            # Check if group exists and belongs to user
            check_query = """
                SELECT name FROM watchlist_groups
                WHERE id = %s AND user_id = %s
            """
            existing = DatabaseManager.execute_query(
                check_query,
                (group_id, user_id),
                fetch=True
            )

            if not existing or len(existing) == 0:
                raise ValueError("分组不存在或不属于当前用户")

            # Prevent deleting default group
            if existing[0]['name'] == '未分类':
                raise ValueError("不能删除默认分组")

            # Delete group (stocks will have group_id set to NULL via ON DELETE SET NULL)
            delete_query = """
                DELETE FROM watchlist_groups
                WHERE id = %s AND user_id = %s
            """
            DatabaseManager.execute_query(delete_query, (group_id, user_id), fetch=False)

            return True

        except ValueError as e:
            logger.warning(f"Validation error deleting group {group_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting group {group_id} for user {user_id}: {e}")
            raise

    @staticmethod
    def ensure_default_group(user_id: str) -> Dict:
        """
        Ensure user has a default "未分类" group.
        Create it if it doesn't exist.

        Args:
            user_id: User ID (UUID)

        Returns:
            Default group dict
        """
        try:
            # Check if default group exists
            check_query = """
                SELECT id, name, color, sort_order, created_at, updated_at
                FROM watchlist_groups
                WHERE user_id = %s AND name = '未分类'
            """
            existing = DatabaseManager.execute_query(check_query, (user_id,), fetch=True)

            if existing and len(existing) > 0:
                return dict(existing[0])

            # Create default group
            insert_query = """
                INSERT INTO watchlist_groups (user_id, name, color, sort_order)
                VALUES (%s, '未分类', '#999999', 0)
                RETURNING id, name, color, sort_order, created_at, updated_at
            """
            results = DatabaseManager.execute_query(insert_query, (user_id,), fetch=True)

            if results and len(results) > 0:
                logger.info(f"Created default group for user {user_id}")
                return dict(results[0])
            else:
                raise Exception("创建默认分组失败")

        except Exception as e:
            logger.error(f"Error ensuring default group for user {user_id}: {e}")
            raise
