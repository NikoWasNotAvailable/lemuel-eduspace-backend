import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "mysql+pymysql://root:password@localhost:3306/eduspace"
    async_database_url: str = "mysql+aiomysql://root:password@localhost:3306/eduspace"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    app_name: str = "Lemuel EduSpace Backend"
    debug: bool = True
    version: str = "1.0.0"
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"

settings = Settings()