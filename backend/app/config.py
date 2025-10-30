"""Application configuration."""

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # API
    API_VERSION = os.environ.get('API_VERSION', 'v1')

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
