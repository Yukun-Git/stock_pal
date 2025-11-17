"""Authentication service for user login and verification."""

import bcrypt
from typing import Optional, Dict
from app.utils.db import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling user authentication."""

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        """
        Get user by username from database.

        Args:
            username: Username to search for

        Returns:
            User dict if found, None otherwise
        """
        try:
            query = """
                SELECT id, username, email, password_hash, nickname,
                       is_active, created_at, last_login_at
                FROM users
                WHERE username = %s AND is_active = TRUE
            """
            results = DatabaseManager.execute_query(query, (username,), fetch=True)

            if results and len(results) > 0:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user {username}: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """
        Get user by ID from database.

        Args:
            user_id: User ID to search for

        Returns:
            User dict if found, None otherwise
        """
        try:
            query = """
                SELECT id, username, email, nickname,
                       is_active, created_at, last_login_at
                FROM users
                WHERE id = %s AND is_active = TRUE
            """
            results = DatabaseManager.execute_query(query, (user_id,), fetch=True)

            if results and len(results) > 0:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {e}")
            return None

    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        """
        Verify a plain password against a bcrypt hash.

        Args:
            plain_password: Plain text password
            password_hash: Bcrypt password hash

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User dict (without password_hash) if authentication succeeds,
            None otherwise
        """
        # Get user from database
        user = AuthService.get_user_by_username(username)

        if not user:
            logger.info(f"Authentication failed: user {username} not found")
            return None

        # Verify password
        password_hash = user.get('password_hash')
        if not password_hash or not AuthService.verify_password(password, password_hash):
            logger.info(f"Authentication failed: invalid password for user {username}")
            return None

        # Update last login time
        try:
            update_query = """
                UPDATE users
                SET last_login_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            DatabaseManager.execute_query(update_query, (user['id'],), fetch=False)
        except Exception as e:
            logger.warning(f"Failed to update last_login_at for user {username}: {e}")

        # Remove password_hash from returned user data
        user_data = {k: v for k, v in user.items() if k != 'password_hash'}

        logger.info(f"User {username} authenticated successfully")
        return user_data

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """
        Hash a plain password using bcrypt.

        Args:
            plain_password: Plain text password

        Returns:
            Bcrypt password hash
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
