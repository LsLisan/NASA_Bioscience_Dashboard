"""
Configuration settings for NASA Bioscience Explorer
"""

import os
from pathlib import Path

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nasa-bioscience-explorer-dev-key'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Application settings
    APP_NAME = "NASA Bioscience Explorer"
    VERSION = "1.0.0"
    
    # File paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    PDF_DIR = DATA_DIR / 'pdfs'
    CACHE_DIR = DATA_DIR / 'cache'
    
    # CSV file settings
    CSV_FILE = DATA_DIR / 'SB_publication_PMC.csv'
    
    # PDF processing settings
    MAX_PDF_SIZE_MB = 50  # Maximum PDF file size in MB
    PDF_TIMEOUT = 30      # Timeout for PDF download in seconds
    MAX_RETRIES = 3       # Maximum download retries
    
    # Search settings
    RESULTS_PER_PAGE = 10
    MAX_RESULTS_PER_PAGE = 50
    
    # Cache settings
    CACHE_EXPIRY_HOURS = 24  # Hours before cache expires
    
    # Request settings
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    @classmethod
    def init_app(cls, app):
        """Initialize the Flask app with this config"""
        # Create necessary directories
        cls.PDF_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Set Flask config
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['DEBUG'] = cls.DEBUG

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Use environment variables for sensitive settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-in-production'
    
class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}