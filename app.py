from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import time
import uvicorn
from collections import defaultdict
from datetime import datetime
import asyncio

app = FastAPI()

REQUESTS_TOTAL = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ERRORS_TOTAL = Counter('http_errors_total', 'Total errors', ['endpoint'])
UP = Gauge('up', 'Application up status')
UP.set(1)

app_requests_total = 0
app_errors_total = 0
app_latency_total = 0.0
app_latency_count = 0
app_uptime = 0
requests_by_endpoint = defaultdict(int)
errors_by_endpoint = defaultdict(int)

start_time = time.time()
metrics_lock = asyncio.Lock()

def update_zabbix_metrics():
    global app_uptime
    app_uptime = time.time() - start_time

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/metrics")
async def zabbix_metrics():
    async with metrics_lock:
        update_zabbix_metrics()
        avg_latency = app_latency_total / max(app_latency_count, 1)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "app_requests_total": app_requests_total,
            "app_errors_total": app_errors_total,
            "app_latency_avg": round(avg_latency, 3),
            "app_uptime": round(app_uptime, 1),
            "requests_by_endpoint": dict(requests_by_endpoint),
            "errors_by_endpoint": dict(errors_by_endpoint),
            "up": 1
        }

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    global app_requests_total, requests_by_endpoint, app_errors_total, app_latency_total, app_latency_count, app_uptime
    start_time_req = time.time()
    endpoint = request.url.path
    method = request.method

    async with metrics_lock:
        requests_by_endpoint[endpoint] += 1
        app_requests_total += 1

    try:
        response = await call_next(request)
        status = str(response.status_code)
        REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
        duration = time.time() - start_time_req
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        async with metrics_lock:
            app_latency_total += duration
            app_latency_count += 1
        return response
    except Exception as e:
        async with metrics_lock:
            errors_by_endpoint[endpoint] += 1
            app_errors_total += 1
        ERRORS_TOTAL.labels(endpoint=endpoint).inc()
        raise

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/data")
async def get_data():
    time.sleep(0.1)
    return {"data": [1, 2, 3]}

@app.post("/create")
async def create_item():
    time.sleep(0.05)
    return {"id": "123", "created": True}

@app.get("/list")
async def list_items():
    time.sleep(0.2)
    return {"items": [{"id": 1}, {"id": 2}]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
