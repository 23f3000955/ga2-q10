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
    allow_origin_regex="https://.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = {}

@app.middleware("http")
async def middleware(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")
    if request_id is None or request_id == "":
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

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
            response.headers["X-Request-ID"] = request_id
            return response

        clients[client].append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):

    response = JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request.state.request_id,
        }
    )

    response.headers["X-Request-ID"] = request.state.request_id

    return response