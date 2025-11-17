"""Authentication API endpoints."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt
from app.services.auth_service import AuthService
from app.utils.auth import jwt_required_custom
import logging

logger = logging.getLogger(__name__)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.

    Request body:
        {
            "username": "test",
            "password": "test123"
        }

    Returns:
        200: Login successful with JWT token
        400: Missing required fields
        401: Invalid credentials
    """
    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "invalid_request",
                "message": "请求体不能为空"
            }), 400

        username = data.get('username')
        password = data.get('password')

        # Validate input
        if not username or not password:
            return jsonify({
                "error": "missing_fields",
                "message": "用户名和密码不能为空"
            }), 400

        # Authenticate user
        user = AuthService.authenticate_user(username, password)

        if not user:
            return jsonify({
                "error": "invalid_credentials",
                "message": "用户名或密码错误"
            }), 401

        # Create JWT token
        access_token = create_access_token(identity=user['id'])

        # Return token and user info
        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 86400,  # 24 hours in seconds
            "user": {
                "id": user['id'],
                "username": user['username'],
                "nickname": user.get('nickname'),
                "email": user.get('email')
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "登录失败，请稍后重试"
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required_custom
def get_current_user(current_user):
    """
    Get current user information.

    Requires:
        Authorization: Bearer <token>

    Returns:
        200: User information
        401: Unauthorized
    """
    try:
        return jsonify({
            "id": current_user['id'],
            "username": current_user['username'],
            "nickname": current_user.get('nickname'),
            "email": current_user.get('email'),
            "created_at": current_user.get('created_at').isoformat() if current_user.get('created_at') else None,
            "last_login_at": current_user.get('last_login_at').isoformat() if current_user.get('last_login_at') else None
        }), 200

    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "获取用户信息失败"
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required_custom
def logout(current_user):
    """
    User logout endpoint.

    Note: In this simple implementation, logout is handled client-side
    by deleting the token. Server-side token blacklist is not implemented.

    Requires:
        Authorization: Bearer <token>

    Returns:
        200: Logout successful
    """
    logger.info(f"User {current_user['username']} logged out")

    return jsonify({
        "message": "成功登出"
    }), 200
