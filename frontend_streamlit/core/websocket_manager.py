import json
import threading
import logging
from typing import Optional

logger = logging.getLogger("StreamlitWebSocket")

_alert_store = []
_ws_lock = threading.Lock()
_ws_thread_started = False


def _ws_listener():
    try:
        import websocket
    except ImportError:
        logger.error("websocket-client not installed. Run: pip install websocket-client")
        return

    def on_message(ws, message):
        global _alert_store
        try:
            data = json.loads(message)
            with _ws_lock:
                _alert_store.insert(0, data)
                if len(_alert_store) > 50:
                    _alert_store = _alert_store[:50]
        except Exception as e:
            logger.error(f"WS parse error: {e}")

    def on_error(ws, error):
        logger.error(f"WS error: {error}")

    def on_close(ws, close_status, close_msg):
        logger.info("WS connection closed")

    def on_open(ws):
        logger.info("WS connected to backend alerts")

    ws = websocket.WebSocketApp(
        "ws://localhost:8000/ws/alerts",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever(reconnect=5)


def init_websocket():
    global _ws_thread_started
    if not _ws_thread_started:
        thread = threading.Thread(target=_ws_listener, daemon=True)
        thread.start()
        _ws_thread_started = True
        logger.info("WebSocket listener thread started")


def get_live_alerts():
    with _ws_lock:
        return list(_alert_store)


def clear_alerts():
    global _alert_store
    with _ws_lock:
        _alert_store = []
