from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio

class PocketOptionClient:
    def __init__(self, ssid: str, is_demo: bool = True):
        self.client = AsyncPocketOptionClient(ssid, is_demo=is_demo, enable_logging=False)
        self.connected = False
        
    async def connect(self):
        try:
            await self.client.connect()
            self.connected = True
            print("✅ Успішно підключено до Pocket Option")
            return True
        except Exception as e:
            print(f"❌ Помилка підключення: {e}")
            return False
    
    async def disconnect(self):
        await self.client.disconnect()
        self.connected = False
        
    async def is_connected(self) -> bool:
        return self.connected
    
    async def get_candles(self, asset: str, timeframe: int, count: int = 100):
        """Отримати свічки для аналізу"""
        try:
            candles = await self.client.get_candles(asset, timeframe, count=count)
            return candles
        except Exception as e:
            print(f"Помилка отримання свічок для {asset}: {e}")
            return None
    
    async def get_candles_dataframe(self, asset: str, timeframe: int, count: int = 100):
        """Отримати свічки як DataFrame"""
        try:
            df = await self.client.get_candles_dataframe(asset, timeframe, count=count)
            return df
        except Exception as e:
            print(f"Помилка створення DataFrame для {asset}: {e}")
            return None
    
    async def get_available_assets(self) -> List[str]:
        """Отримати список доступних активів"""
        # Тут можна повернути фіксований список або отримати з API
        return [
            "GBPJPY_otc", "EURUSD_otc", "USDJPY_otc",
            "BTCUSD", "ETHUSD", "XAUUSD_otc",
            "SP500_otc", "NASUSD_otc"
        ]
    
    async def get_balance(self):
        """Отримати баланс"""
        try:
            balance = await self.client.get_balance()
            return balance
        except Exception as e:
            print(f"Помилка отримання балансу: {e}")
            return None
