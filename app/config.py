from dotenv import load_dotenv
import os

load_dotenv() 

class Settings:
    DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:1234@localhost:5432/assignments_db",
    )
    print("Using DATABASE_URL:", os.getenv(
    "DATABASE_URL"))
    APP_ENV: str = os.getenv("APP_ENV", "dev")


settings = Settings()