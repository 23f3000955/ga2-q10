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
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

clients = {}


@app.middleware("http")
async def request_context(request: Request, call_next):

    # Request ID
    req_id = request.headers.get("X-Request-ID")
    if not req_id:
        req_id = str(uuid.uuid4())

    request.state.req_id = req_id

    # Rate limiting
    client = request.headers.get("X-Client-Id")
    if client:
        now = time.time()

        clients.setdefault(client, [])

        clients[client] = [
            t for t in clients[client]
            if now - t < WINDOW
        ]

        if len(clients[client]) >= RATE_LIMIT:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "10"},
            )
            response.headers["X-Request-ID"] = req_id
            return response

        clients[client].append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = req_id

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.req_id
    }