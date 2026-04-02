import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///pos_system.db')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    SESSION_TIMEOUT = timedelta(minutes=30)

    # Payment gateway configurations
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    MOMO_API_KEY = os.getenv('MOMO_API_KEY')
    MOMO_API_USER = os.getenv('MOMO_API_USER')

    # Redis configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

    # Application settings
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

    # Production-specific settings
    SESSION_TIMEOUT = timedelta(minutes=15)  # Shorter sessions in prod

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    LOG_LEVEL = 'DEBUG'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class based on environment."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    return config.get(config_name, config['default'])</content>
<parameter name="filePath">c:\Users\dauda\Desktop\websites\SOP\config.py