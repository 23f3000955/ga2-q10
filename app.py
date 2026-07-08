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
    allow_origin_regex=r"https://.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = {}


@app.middleware("http")
async def rate_limit(request: Request, call_next):

    client = request.headers.get("X-Client-Id")

    if client:
        now = time.time()

        clients.setdefault(client, [])

        clients[client] = [
            t for t in clients[client]
            if now - t < WINDOW
        ]

        if len(clients[client]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "10"},
            )

        clients[client].append(now)

    return await call_next(request)


@app.get("/ping")
async def ping(request: Request):

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    response = JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request_id
        }
    )

    response.headers["X-Request-ID"] = request_id

    return response