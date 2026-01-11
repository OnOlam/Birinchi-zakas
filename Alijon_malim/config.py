"""
Configuration for Flask Application
Development va Production sozlamalari
"""

import os
from datetime import timedelta


class Config:
    """Base configuration"""
    
    # Secret Key - production uchun environment variable orqali
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///attendance.db')
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'  # Auto set
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Debug mode
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    
    # Security
    WTF_CSRF_ENABLED = True
    
    # Flask environment
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Additional settings
    PREFERRED_URL_SCHEME = 'https' if os.environ.get('FLASK_ENV') == 'production' else 'http'


class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Local SQLite database
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "attendance.db")}'
    
    # Security (development uchun)
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Production security
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    
    # SECRET_KEY ni environment dan olish (agar bo'lmasa warning)
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            import warnings
            warnings.warn("SECRET_KEY environment variable is not set! Using fallback key.")
            return 'fallback-key-please-set-secret-key'
        return key


class TestingConfig(Config):
    """Testing configuration"""
    
    DEBUG = False
    TESTING = True
    FLASK_ENV = 'testing'
    
    # In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Security (testing uchun)
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig  # Agar environment aniqlanmasa, development ishlatiladi
}


def get_config(env=None):
    """
    Get configuration based on environment
    
    Args:
        env: Environment name ('development', 'production', 'testing')
        
    Returns:
        Configuration class
    """
    if env is None:
        # Render'da RENDER environment variable bor, uni tekshirish
        if os.environ.get('RENDER'):
            env = 'production'
        else:
            env = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(env, config['default'])
