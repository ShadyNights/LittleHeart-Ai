from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("ErrorHandler")

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global Exception: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error. Please contact support."})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP Exception: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
