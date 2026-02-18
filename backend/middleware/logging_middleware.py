import logging
import time
from fastapi import Request
from backend.config import settings

def setup_logging():
    try:
        from pythonjsonlogger import jsonlogger
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(settings.LOG_LEVEL)
        if logging.getLogger().hasHandlers():
            logging.getLogger().handlers.clear()
            logging.getLogger().addHandler(handler)
    except ImportError:
        logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    logger = logging.getLogger("Middleware")
    logger.info(f"Incoming Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request Completed: {response.status_code} (Time: {process_time:.4f}s)")
        return response
    except Exception as e:
        logger.error(f"Request Failed: {e}")
        raise e
