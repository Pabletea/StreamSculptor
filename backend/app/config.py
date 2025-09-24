import os
from urllib.parse import urlparse

class Config:
    # Redis configuration
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    # PostgreSQL configuration
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    
    # MinIO configuration
    MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"
    
    # Whisper service
    WHISPER_URL = os.environ.get("WHISPER_URL", "http://localhost:5000")
    
    # Environment
    ENVIRONMENT = os.environ.get("RAILWAY_ENVIRONMENT", "development")
    
    @classmethod
    def get_redis_url(cls):
        """Get formatted Redis URL for Celery"""
        return cls.REDIS_URL
    
    @classmethod
    def get_minio_endpoint(cls):
        """Clean MinIO endpoint (remove protocol if present)"""
        endpoint = cls.MINIO_ENDPOINT
        if "://" in endpoint:
            endpoint = endpoint.split("://")[1]
        return endpoint
    
    @classmethod
    def is_production(cls):
        return cls.ENVIRONMENT == "production"