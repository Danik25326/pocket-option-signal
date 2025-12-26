from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager

from config import settings
from pocket_api import PocketOptionClient
from ai_analyzer import AIAnalyzer
from signal_generator import SignalGenerator

# Ініціалізація клієнтів
pocket_client = None
ai_analyzer = None
signal_generator = None
active_connections = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск при старті
    global pocket_client, ai_analyzer, signal_generator
    
    print("🚀 Запуск Pocket Option клієнта...")
    pocket_client = PocketOptionClient(settings.POCKET_SSID, settings.IS_DEMO)
    await pocket_client.connect()
    
    print("🧠 Ініціалізація AI аналізатора...")
    ai_analyzer = AIAnalyzer(settings.GROQ_API_KEY)
    
    print("📡 Створення генератора сигналів...")
    signal_generator = SignalGenerator(pocket_client, ai_analyzer)
    
    # Запуск фонового процесу генерації сигналів
    asyncio.create_task(signal_generator.start_generation())
    
    yield
    
    # Завершення при зупинці
    await pocket_client.disconnect()

app = FastAPI(lifespan=lifespan, title="Pocket Option Signal Bot")

# Дозволити CORS для фронтенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "running", "service": "Pocket Option Signal Bot"}

@app.get("/health")
async def health_check():
    if pocket_client and await pocket_client.is_connected():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    return {"status": "unhealthy", "error": "Not connected to Pocket Option"}

@app.get("/signals")
async def get_recent_signals(limit: int = 10):
    """Отримати останні сигнали"""
    return signal_generator.get_recent_signals(limit)

@app.get("/assets")
async def get_available_assets():
    """Отримати доступні активи"""
    return await pocket_client.get_available_assets()

@app.get("/status")
async def get_status():
    """Статус системи"""
    return {
        "connected": await pocket_client.is_connected(),
        "last_signal_time": signal_generator.last_signal_time,
        "total_signals_generated": signal_generator.total_signals,
        "signals_today": signal_generator.get_signals_today()
    }

# WebSocket для реального часу
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Отримуємо повідомлення від клієнта
            data = await websocket.receive_text()
            
            if data == "get_signals":
                signals = signal_generator.get_recent_signals(10)
                await websocket.send_json({
                    "type": "signals",
                    "data": signals,
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")

# Функція для відправки сигналів всім підключеним клієнтам
async def broadcast_signal(signal):
    for connection in active_connections:
        try:
            await connection.send_json({
                "type": "new_signal",
                "data": signal,
                "timestamp": datetime.now().isoformat()
            })
        except:
            continue

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
