from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Doc Platform"
    
    # DeepSeek API配置
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_API_ENDPOINT: str = os.getenv("AI_API_ENDPOINT", "https://api.deepseek.com/v1/chat/completions")
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 数据库配置
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ai_doc_platform")
    
    # 多种AI服务设置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_ENDPOINT: str = os.getenv("OPENAI_API_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_API_ENDPOINT: str = os.getenv("CLAUDE_API_ENDPOINT", "https://api.anthropic.com/v1/messages")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 