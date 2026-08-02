from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router


app = FastAPI(
    title="AI Employee OS"
)


# Allow the Next.js frontend to call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    router,
    prefix="/api/v1"
)


@app.get("/")
def root():

    return {
        "name":"AI Employee OS",
        "status":"running"
    }