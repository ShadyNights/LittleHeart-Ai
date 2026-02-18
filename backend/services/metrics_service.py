from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
import logging
from typing import Dict, Any

logger = logging.getLogger("MetricsService")

REQUEST_COUNT = Counter(
    "clinical_requests_total", 
    "Total clinical analysis requests", 
    ["method", "endpoint", "status"]
)

LATENCY_HISTOGRAM = Histogram(
    "clinical_latency_seconds", 
    "Latency of clinical engines in seconds", 
    ["engine"]
)

ERROR_COUNT = Counter(
    "clinical_errors_total", 
    "Total clinical system errors", 
    ["engine", "error_type"]
)

ALERT_COUNT = Counter(
    "clinical_alerts_total", 
    "Total medical alerts triggered", 
    ["risk_level"]
)

class MetricsService:
    _failure_history = {}

    @staticmethod
    def record_latency(engine: str, duration: float):
        LATENCY_HISTOGRAM.labels(engine=engine).observe(duration)

    @staticmethod
    def record_error(engine: str, error_type: str):
        ERROR_COUNT.labels(engine=engine, error_type=error_type).inc()
        MetricsService._track_health(engine, success=False)

    @staticmethod
    def record_request(status: int):
        REQUEST_COUNT.labels(method="POST", endpoint="/analyze", status=status).inc()

    @staticmethod
    def record_success(engine: str):
        MetricsService._track_health(engine, success=True)

    @classmethod
    def _track_health(cls, engine: str, success: bool):
        now = time.time()
        if engine not in cls._failure_history:
            cls._failure_history[engine] = []
        
        cls._failure_history[engine].append((now, success))
        cls._failure_history[engine] = [x for x in cls._failure_history[engine] if now - x[0] < 600]
        
        data = cls._failure_history[engine]
        if len(data) >= 10:
            failures = len([x for x in data if not x[1]])
            rate = failures / len(data)
            if rate > 0.1:
                 logger.critical(f"CRITICAL_SYS_ALERT: {engine} failure rate is {rate*100:.1f}%!")

    @classmethod
    def get_health_report(cls) -> Dict[str, Any]:
        report = {}
        for engine, data in cls._failure_history.items():
            if not data: continue
            failures = len([x for x in data if not x[1]])
            report[engine] = {
                "status": "UNHEALTHY" if (failures / len(data)) > 0.1 else "HEALTHY",
                "error_rate": f"{(failures / len(data)) * 100:.1f}%",
                "sample_size": len(data)
            }
        return report

def metrics_endpoint():
    health = MetricsService.get_health_report()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
