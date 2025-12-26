import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

class SignalGenerator:
    def __init__(self, pocket_client, ai_analyzer):
        self.pocket_client = pocket_client
        self.ai_analyzer = ai_analyzer
        self.signals = []
        self.last_signal_time = None
        self.total_signals = 0
        self.min_confidence = 0.7
        
    async def generate_signal(self, asset: str, timeframe: int):
        """Згенерувати сигнал для конкретного активу та таймфрейму"""
        
        # Отримати дані
        df = await self.pocket_client.get_candles_dataframe(asset, timeframe, count=100)
        
        if df is None or df.empty:
            return None
        
        # AI аналіз
        analysis = await self.ai_analyzer.analyze_market(asset, timeframe, df)
        
        # Перевірити впевненість
        if analysis['confidence'] < self.min_confidence:
            return None
        
        # Створити сигнал
        signal = {
            "id": f"{asset}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "asset": asset,
            "asset_name": self._get_asset_name(asset),
            "timeframe": timeframe,
            "timeframe_text": f"{timeframe//60} хв" if timeframe >= 60 else f"{timeframe} сек",
            "direction": analysis['direction'],
            "confidence": round(analysis['confidence'] * 100, 1),  # У відсотках
            "reason": analysis['reason'],
            "entry_price": analysis['entry_price'],
            "stop_loss": analysis['stop_loss'],
            "take_profit": analysis['take_profit'],
            "time_to_expire": analysis['time_to_expire'],
            "indicators": analysis['indicators'],
            "timestamp": datetime.now().isoformat(),
            "human_time": datetime.now().strftime("%H:%M:%S")
        }
        
        # Додати до історії
        self.signals.append(signal)
        self.last_signal_time = datetime.now()
        self.total_signals += 1
        
        # Зберегти останні 100 сигналів
        if len(self.signals) > 100:
            self.signals = self.signals[-100:]
        
        return signal
    
    async def generate_all_signals(self):
        """Згенерувати сигнали для всіх активів та таймфреймів"""
        from config import settings
        
        all_signals = []
        
        for asset in settings.ASSETS:
            for timeframe in settings.TIME_FRAMES:
                try:
                    signal = await self.generate_signal(asset, timeframe)
                    if signal:
                        all_signals.append(signal)
                        print(f"✅ Сигнал: {signal['asset']} {signal['timeframe_text']} {signal['direction']} ({signal['confidence']}%)")
                except Exception as e:
                    print(f"❌ Помилка генерації сигналу для {asset}: {e}")
                
                # Невелика затримка між запитами
                await asyncio.sleep(1)
        
        # Сортувати за впевненістю
        all_signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        return all_signals
    
    async def start_generation(self):
        """Запустити періодичну генерацію сигналів"""
        from config import settings
        
        print(f"⏰ Запуск генератора сигналів з інтервалом {settings.SIGNAL_INTERVAL} секунд")
        
        while True:
            try:
                print(f"\n🔍 Генерація сигналів {datetime.now().strftime('%H:%M:%S')}...")
                signals = await self.generate_all_signals()
                
                if signals:
                    print(f"📊 Знайдено {len(signals)} сигналів")
                    # Тут можна додати відправку на фронтенд через WebSocket
                else:
                    print("📭 Сигналів не знайдено")
                    
            except Exception as e:
                print(f"⚠️ Помилка в генераторі: {e}")
            
            # Чекати заданий інтервал
            await asyncio.sleep(settings.SIGNAL_INTERVAL)
    
    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """Отримати останні сигнали"""
        recent = self.signals[-limit:] if self.signals else []
        return recent
    
    def get_signals_today(self) -> List[Dict]:
        """Отримати сигнали за сьогодні"""
        today = datetime.now().date()
        today_signals = [
            s for s in self.signals 
            if datetime.fromisoformat(s['timestamp']).date() == today
        ]
        return today_signals
    
    def _get_asset_name(self, asset_code: str) -> str:
        """Отримати читабельну назву активу"""
        names = {
            "GBPJPY_otc": "GBP/JPY OTC",
            "EURUSD_otc": "EUR/USD OTC",
            "BTCUSD": "Bitcoin/USD",
            "XAUUSD_otc": "Gold/USD OTC",
            "SP500_otc": "S&P 500 OTC"
        }
        return names.get(asset_code, asset_code)
