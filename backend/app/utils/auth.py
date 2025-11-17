"""JWT authentication utilities."""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)


def jwt_required_custom(fn):
    """
    Custom JWT required decorator that also fetches current user.

    This decorator:
    1. Verifies JWT token in request
    2. Fetches current user from database
    3. Passes user as first argument to the wrapped function

    Usage:
        @jwt_required_custom
        def my_endpoint(current_user):
            return jsonify({"user_id": current_user['id']})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()

            # Get user ID from token
            user_id = get_jwt_identity()

            # Fetch user from database
            current_user = AuthService.get_user_by_id(user_id)

            if not current_user:
                logger.warning(f"JWT token valid but user {user_id} not found")
                return jsonify({
                    "error": "user_not_found",
                    "message": "用户不存在或已被禁用"
                }), 401

            # Call the wrapped function with current_user
            return fn(current_user, *args, **kwargs)

        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            return jsonify({
                "error": "authentication_failed",
                "message": "认证失败"
            }), 401

    return wrapper


def get_current_user():
    """
    Get current authenticated user from JWT token.

    Returns:
        User dict if authenticated, None otherwise
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        return AuthService.get_user_by_id(user_id)
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None
