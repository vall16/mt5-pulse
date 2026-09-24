import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# --------------------------------------------------
# ENV
# --------------------------------------------------
load_dotenv()

REMOTE_MT5_API_URL = os.getenv("REMOTE_MT5_API_URL", "http://127.0.0.1:8000/")
API_PORT = int(os.getenv("API_PORT", os.getenv("FASTAPI_PORT", 8080)))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

if CORS_ORIGINS == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in CORS_ORIGINS.split(",")]

# --------------------------------------------------
# APP
# --------------------------------------------------
app = FastAPI(title="Trading API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def proxy_request(method: str, path: str, request: Request):
    url = f"{REMOTE_MT5_API_URL.rstrip('/')}/{path.lstrip('/')}"

    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=request.query_params, timeout=30)
        elif method == "POST":
            body = None
            try:
                body = request._body  # type: ignore
            except Exception:
                pass
            resp = requests.post(url, headers=headers, data=body, timeout=30)
        else:
            return JSONResponse(status_code=405, content={"error": "Method not allowed"})

        return JSONResponse(status_code=resp.status_code, content=resp.json())

    except requests.exceptions.RequestException as e:
        return JSONResponse(status_code=502, content={"error": "Remote MT5 API unreachable", "details": str(e)})

# --------------------------------------------------
# ROUTES (PROXY)
# --------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "remote": REMOTE_MT5_API_URL}

@app.post("/login")
async def login(request: Request):
    return proxy_request("POST", "/login", request)

@app.get("/positions")
async def positions(request: Request):
    return proxy_request("GET", "/positions", request)

@app.get("/symbols")
async def symbols(request: Request):
    return proxy_request("GET", "/symbols", request)

@app.get("/symbols/active")
async def symbols_active(request: Request):
    return proxy_request("GET", "/symbols/active", request)

@app.post("/order")
async def order(request: Request):
    return proxy_request("POST", "/order", request)

@app.post("/close_order/{ticket}")
async def close_order(ticket: int, request: Request):
    return proxy_request("POST", f"/close_order/{ticket}", request)

@app.post("/close_order_by_symbol")
async def close_order_by_symbol(request: Request):
    return proxy_request("POST", "/close_order_by_symbol", request)

@app.get("/terminal_info")
async def terminal_info(request: Request):
    return proxy_request("GET", "/terminal_info", request)

@app.post("/get_rates_range")
async def get_rates_range(request: Request):
    return proxy_request("POST", "/get_rates_range", request)

# --------------------------------------------------
# ERROR HANDLER
# --------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)},
    )

# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=False,
    )
