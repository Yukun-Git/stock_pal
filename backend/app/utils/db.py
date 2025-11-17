"""PostgreSQL database connection utilities."""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """PostgreSQL database configuration."""

    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = int(os.getenv('POSTGRES_PORT', 5432))
        self.user = os.getenv('POSTGRES_USER', 'stockpal')
        self.password = os.getenv('POSTGRES_PASSWORD', 'stockpal_dev_2024')
        self.database = os.getenv('POSTGRES_DB', 'stockpal')

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_connection_params(self) -> dict:
        """Get connection parameters as a dict."""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database
        }


class DatabaseManager:
    """PostgreSQL database connection manager."""

    _config = None

    @classmethod
    def get_config(cls) -> DatabaseConfig:
        """Get database configuration (singleton)."""
        if cls._config is None:
            cls._config = DatabaseConfig()
        return cls._config

    @classmethod
    @contextmanager
    def get_connection(cls, dict_cursor: bool = False):
        """
        Get a database connection (context manager).

        Args:
            dict_cursor: If True, use RealDictCursor for dict-like rows

        Yields:
            Database connection
        """
        config = cls.get_config()
        conn = None
        try:
            conn_params = config.get_connection_params()
            if dict_cursor:
                conn_params['cursor_factory'] = RealDictCursor

            conn = psycopg2.connect(**conn_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @classmethod
    def execute_query(cls, query: str, params: Optional[tuple] = None, fetch: bool = True):
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Query parameters (optional)
            fetch: Whether to fetch results

        Returns:
            Query results if fetch=True, else None
        """
        with cls.get_connection(dict_cursor=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                return None

    @classmethod
    def execute_many(cls, query: str, params_list: list):
        """
        Execute a SQL query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        with cls.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
