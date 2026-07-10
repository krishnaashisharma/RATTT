"""
Configuration management for the backend.
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://rdm:rdm@postgres:5432/rdm"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 1
    DEVICE_JWT_EXPIRATION_HOURS: int = 1
    
    # TLS
    TLS_CERT_PATH: str = "/etc/remote-device-mgmt/server.crt"
    TLS_KEY_PATH: str = "/etc/remote-device-mgmt/server.key"
    TLS_CA_PATH: str = "/etc/remote-device-mgmt/ca.crt"
    
    # Enrolment
    ENROLMENT_TOKEN_EXPIRATION_MINUTES: int = 30
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8443
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
