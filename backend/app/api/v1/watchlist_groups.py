"""Watchlist groups API endpoints."""

from flask import request
from flask_restful import Resource
from app.services.watchlist_group_service import WatchlistGroupService
from app.utils.auth import jwt_required_resource
from app.utils.response import convert_to_json_serializable
import logging

logger = logging.getLogger(__name__)


class WatchlistGroupsResource(Resource):
    """Resource for watchlist groups operations."""

    @jwt_required_resource
    def get(self, current_user):
        """
        Get user's watchlist groups.

        Query params:
            include_counts (optional): Whether to include stock count for each group (true/false), default: false

        Returns:
            200: Success with groups data
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']

            # Parse query parameters
            include_counts = request.args.get('include_counts', 'false').lower() == 'true'

            # Get groups
            groups = WatchlistGroupService.get_user_groups(
                user_id=user_id,
                include_counts=include_counts
            )

            return {
                'status': 'success',
                'data': {
                    'groups': convert_to_json_serializable(groups),
                    'total': len(groups)
                }
            }, 200

        except Exception as e:
            logger.error(f"Error getting groups for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '获取分组列表失败',
                'code': 'GROUPS_FETCH_ERROR'
            }, 500

    @jwt_required_resource
    def post(self, current_user):
        """
        Create a new watchlist group.

        Request body:
            {
                "name": "科技板块",
                "color": "#52c41a" (optional),
                "sort_order": 10 (optional)
            }

        Returns:
            201: Group created successfully
            400: Validation error
            409: Group name already exists
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
            name = data.get('name')

            if not name:
                return {
                    'status': 'error',
                    'error': '分组名称不能为空',
                    'code': 'MISSING_REQUIRED_FIELDS'
                }, 400

            # Optional fields
            color = data.get('color')
            sort_order = data.get('sort_order')

            # Create group
            result = WatchlistGroupService.create_group(
                user_id=user_id,
                name=name,
                color=color,
                sort_order=sort_order
            )

            return {
                'status': 'success',
                'data': convert_to_json_serializable(result),
                'message': '分组创建成功'
            }, 201

        except ValueError as e:
            error_msg = str(e)
            if '已存在' in error_msg:
                code = 'GROUP_NAME_EXISTS'
                status_code = 409
            else:
                code = 'VALIDATION_ERROR'
                status_code = 400

            return {
                'status': 'error',
                'error': error_msg,
                'code': code
            }, status_code

        except Exception as e:
            logger.error(f"Error creating group for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '创建分组失败',
                'code': 'CREATE_GROUP_ERROR'
            }, 500


class WatchlistGroupResource(Resource):
    """Resource for individual watchlist group operations."""

    @jwt_required_resource
    def put(self, current_user, group_id):
        """
        Update a watchlist group.

        Args:
            group_id: Group ID

        Request body:
            {
                "name": "科技龙头" (optional),
                "color": "#722ed1" (optional),
                "sort_order": 2 (optional)
            }

        Returns:
            200: Update successful
            400: Validation error
            404: Group not found
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

            # Update group
            result = WatchlistGroupService.update_group(
                user_id=user_id,
                group_id=group_id,
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
            elif '不能修改' in error_msg or '不能删除' in error_msg:
                code = 'FORBIDDEN'
                status_code = 400
            elif '已存在' in error_msg:
                code = 'GROUP_NAME_EXISTS'
                status_code = 409
            else:
                code = 'VALIDATION_ERROR'
                status_code = 400

            return {
                'status': 'error',
                'error': error_msg,
                'code': code
            }, status_code

        except Exception as e:
            logger.error(f"Error updating group {group_id} for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '更新失败',
                'code': 'UPDATE_ERROR'
            }, 500

    @jwt_required_resource
    def delete(self, current_user, group_id):
        """
        Delete a watchlist group.

        Args:
            group_id: Group ID

        Returns:
            200: Delete successful (stocks moved to default group)
            400: Cannot delete default group
            404: Group not found
            401: Unauthorized
            500: Internal error
        """
        try:
            user_id = current_user['id']

            # Delete group
            WatchlistGroupService.delete_group(user_id, group_id)

            return {
                'status': 'success',
                'message': '分组已删除，内含股票已移至未分类'
            }, 200

        except ValueError as e:
            error_msg = str(e)
            if '不存在' in error_msg or '不属于' in error_msg:
                code = 'NOT_FOUND'
                status_code = 404
            elif '不能删除' in error_msg:
                code = 'CANNOT_DELETE_DEFAULT_GROUP'
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
            logger.error(f"Error deleting group {group_id} for user {current_user['id']}: {e}")
            return {
                'status': 'error',
                'error': '删除失败',
                'code': 'DELETE_ERROR'
            }, 500
