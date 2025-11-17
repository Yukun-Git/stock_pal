"""Application configuration."""

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 24)))
    JWT_ALGORITHM = 'HS256'

    # CORS
    CORS_ORIGINS = os.environ.get(
        'CORS_ORIGINS',
        'http://localhost:4000,http://127.0.0.1:4000,'
        'http://localhost:4080,http://127.0.0.1:4080,'
        'http://localhost:4001,http://127.0.0.1:4001,http://localhost'
    ).split(',')

    # API
    API_VERSION = os.environ.get('API_VERSION', 'v1')

    # Database
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'postgresql://stockpal:stockpal123@localhost:5433/stock_pal_db'
    )

    # Data Source
    DATA_SOURCE = os.environ.get('DATA_SOURCE', 'akshare')
    CACHE_EXPIRY = int(os.environ.get('CACHE_EXPIRY', 3600))

    # Backtest defaults
    DEFAULT_INITIAL_CAPITAL = float(os.environ.get('DEFAULT_INITIAL_CAPITAL', 100000))
    DEFAULT_COMMISSION_RATE = float(os.environ.get('DEFAULT_COMMISSION_RATE', 0.0003))

    # Request timeout
    REQUEST_TIMEOUT = 30


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
