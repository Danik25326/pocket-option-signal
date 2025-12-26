import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Pocket Option
    POCKET_SSID: str = os.getenv("POCKET_SSID")
    IS_DEMO: bool = os.getenv("IS_DEMO", "true").lower() == "true"
    
    # Groq AI
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Сигнали
    MIN_CONFIDENCE: float = 0.7  # 70%
    SIGNAL_INTERVAL: int = 300   # 5 хвилин
    TIME_FRAMES: list = [60, 300]  # 1 хв та 5 хв
    ASSETS: list = [
        "GBPJPY_otc",
        "EURUSD_otc",
        "BTCUSD",
        "XAUUSD_otc",
        "SP500_otc"
    ]
    
    # Максимальна кількість свічок для аналізу
    CANDLES_COUNT: int = 100
    
    class Config:
        env_file = ".env"

settings = Settings()
