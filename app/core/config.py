from dotenv import load_dotenv
import os

load_dotenv()
class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "FastAPI App")
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"

settings = Settings()
