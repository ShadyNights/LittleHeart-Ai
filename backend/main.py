from backend.middleware.logging_middleware import setup_logging
setup_logging()

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.api.analyze import router as analyze_router
from backend.middleware.error_handler import register_exception_handlers
from backend.middleware.logging_middleware import logging_middleware
from backend.middleware.observability import TracingMiddleware
from backend.services.metrics_service import metrics_endpoint
from backend.config import settings
from backend.websocket_manager import manager

limiter = Limiter(key_func=get_remote_address)
ws_logger = logging.getLogger("WebSocketAlerts")

app = FastAPI(
    title="LittleHeart Clinical Risk API",
    version="4.0.0-hardened",
    docs_url="/docs"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
register_exception_handlers(app)

app.add_middleware(TracingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(logging_middleware)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "4.0.0-hardened", "ws_connections": manager.connection_count}

@app.get("/metrics")
def get_metrics():
    return metrics_endpoint()

app.include_router(analyze_router)

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await websocket.accept()
    ws_logger.info("Dashboard WebSocket connected")
    try:
        while True:
            try:
                from backend.services.supabase_service import SupabaseService
                db = SupabaseService()
                if db.client:
                    recent = db.client.table("engine_results").select(
                        "final_risk, created_at"
                    ).order("created_at", desc=True).limit(20).execute()
                    alerts = db.client.table("alerts").select(
                        "id, alert_type, status, created_at, user_id"
                    ).order("created_at", desc=True).limit(10).execute()
                    await websocket.send_json({
                        "type": "DASHBOARD_UPDATE",
                        "recent_results": recent.data if recent.data else [],
                        "recent_alerts": alerts.data if alerts.data else []
                    })
                else:
                    await websocket.send_json({"type": "DASHBOARD_UPDATE", "recent_results": [], "recent_alerts": []})
            except Exception as e:
                ws_logger.error(f"Dashboard data error: {e}")
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        ws_logger.info("Dashboard WebSocket disconnected")
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)