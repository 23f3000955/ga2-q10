from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

EMAIL = "23f3000955@ds.study.iitm.ac.in"

RATE_LIMIT = 14
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-465r66.example.com",
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

clients = {}


@app.middleware("http")
async def middleware(request: Request, call_next):

    # Request Context
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Rate Limiting
    client = request.headers.get("X-Client-Id")

    if client:
        now = time.time()

        if client not in clients:
            clients[client] = []

        clients[client] = [
            t for t in clients[client]
            if now - t < WINDOW
        ]

        if len(clients[client]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        clients[client].append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }