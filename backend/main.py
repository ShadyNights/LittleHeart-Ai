from backend.middleware.logging_middleware import setup_logging
setup_logging()

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
import jwt
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
from backend.utils.auth import Auth

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
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)

app.middleware("http")(logging_middleware)


def _authenticate_ws_token(token: str) -> dict:
    """Verify a JWT token for WebSocket connections. Returns payload or raises."""
    unverified_header = jwt.get_unverified_header(token)
    if "kid" in unverified_header:
        jwks_client = Auth.get_jwks_client()
        if not jwks_client:
            raise ValueError("JWKS Client not initialized")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        key_to_use = signing_key.key
    else:
        key_to_use = settings.SUPABASE_JWT_SECRET
        if not key_to_use:
            raise ValueError("SUPABASE_JWT_SECRET not configured")
            
    payload = jwt.decode(
        token,
        key_to_use,
        algorithms=["HS256", "RS256", "ES256"],
        audience="authenticated",
        options={"verify_exp": True, "verify_nbf": True, "verify_iss": False, "verify_aud": True}
    )
    if "sub" not in payload:
        raise ValueError("Token missing subject claim")
    return payload


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "4.0.0-hardened", "ws_connections": manager.connection_count}

@app.get("/metrics")
def get_metrics():
    return metrics_endpoint()

app.include_router(analyze_router)

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket, token: str = Query(default=None)):
    # Authenticate WebSocket connection via query parameter
    if not token:
        await websocket.close(code=4001, reason="Authentication required. Provide ?token=JWT")
        return
    try:
        _authenticate_ws_token(token)
    except Exception as e:
        await websocket.close(code=4003, reason=f"Authentication failed: {str(e)}")
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket, token: str = Query(default=None)):
    # Authenticate WebSocket connection via query parameter
    if not token:
        await websocket.close(code=4001, reason="Authentication required. Provide ?token=JWT")
        return
    try:
        _authenticate_ws_token(token)
    except Exception as e:
        await websocket.close(code=4003, reason=f"Authentication failed: {str(e)}")
        return

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