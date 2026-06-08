from dotenv import load_dotenv
import os

load_dotenv()
class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "FastAPI App")
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DATABASE_URL_SYNC: str = os.getenv("DATABASE_URL_SYNC", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

settings = Settings()
