from groq import Groq
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
import json

class AIAnalyzer:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model = model
        
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Розрахунок технічних індикаторів"""
        if df.empty:
            return {}
            
        # Прості ковзні середні
        df['SMA_10'] = df['close'].rolling(window=10).mean()
        df['SMA_30'] = df['close'].rolling(window=30).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Останні значення
        latest = df.iloc[-1]
        
        indicators = {
            "sma_10": float(latest['SMA_10']) if not pd.isna(latest['SMA_10']) else None,
            "sma_30": float(latest['SMA_30']) if not pd.isna(latest['SMA_30']) else None,
            "rsi": float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
            "macd": float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
            "signal_line": float(latest['Signal_Line']) if not pd.isna(latest['Signal_Line']) else None,
            "current_price": float(latest['close']),
            "volume": float(latest['volume']),
            "trend": "bullish" if latest['close'] > latest['SMA_10'] else "bearish"
        }
        
        return indicators
    
    async def analyze_market(self, asset: str, timeframe: int, df: pd.DataFrame) -> Dict[str, Any]:
        """Аналіз ринку з використанням AI"""
        
        # Розрахувати технічні індикатори
        indicators = self.calculate_technical_indicators(df)
        
        if df.empty:
            return {
                "asset": asset,
                "timeframe": timeframe,
                "confidence": 0.5,
                "direction": "neutral",
                "analysis": "Недостатньо даних",
                "indicators": {}
            }
        
        # Підготувати дані для AI
        recent_data = df.tail(20)
        price_changes = []
        for i in range(1, 6):
            if len(recent_data) > i:
                change = (recent_data.iloc[-1]['close'] - recent_data.iloc[-i-1]['close']) / recent_data.iloc[-i-1]['close'] * 100
                price_changes.append(round(change, 2))
        
        # Створити промпт для AI
        prompt = f"""
        Ти - професійний трейдер з досвідом аналізу фінансових ринків.
        Проаналізуй наступні дані та дай прогноз:
        
        Актив: {asset}
        Таймфрейм: {timeframe} секунд ({timeframe//60} хвилин)
        
        Технічні індикатори:
        - Поточна ціна: {indicators['current_price']}
        - SMA 10: {indicators['sma_10']}
        - SMA 30: {indicators['sma_30']}
        - RSI: {indicators['rsi']}
        - MACD: {indicators['macd']}
        - Сигнальна лінія: {indicators['signal_line']}
        - Тренд: {indicators['trend']}
        
        Зміни ціни за останні періоди:
        {price_changes}
        
        Дай відповідь у форматі JSON:
        {{
            "direction": "up" або "down",
            "confidence": число від 0 до 1,
            "reason": "коротке пояснення",
            "entry_price": рекомендована ціна входу,
            "stop_loss": рекомендований стоп-лосс,
            "take_profit": рекомендований тейк-профіт,
            "time_to_expire": рекомендований час експірації в секундах
        }}
        
        Важливо: Впевненість (confidence) має бути реальною оцінкою ймовірності.
        """
        
        try:
            # Виклик Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ти професійний трейдер. Давай точні та обґрунтовані прогнози."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Парсинг відповіді
            content = response.choices[0].message.content
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                ai_response = json.loads(content[start_idx:end_idx])
            else:
                ai_response = {
                    "direction": "neutral",
                    "confidence": 0.5,
                    "reason": "Не вдалося проаналізувати",
                    "entry_price": indicators['current_price'],
                    "stop_loss": None,
                    "take_profit": None,
                    "time_to_expire": 300
                }
            
            return {
                "asset": asset,
                "timeframe": timeframe,
                "direction": ai_response.get("direction", "neutral"),
                "confidence": ai_response.get("confidence", 0.5),
                "reason": ai_response.get("reason", ""),
                "entry_price": ai_response.get("entry_price"),
                "stop_loss": ai_response.get("stop_loss"),
                "take_profit": ai_response.get("take_profit"),
                "time_to_expire": ai_response.get("time_to_expire", 300),
                "indicators": indicators,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Помилка AI аналізу: {e}")
            return {
                "asset": asset,
                "timeframe": timeframe,
                "direction": "neutral",
                "confidence": 0.5,
                "reason": f"Помилка аналізу: {str(e)}",
                "indicators": indicators,
                "timestamp": datetime.now().isoformat()
            }
