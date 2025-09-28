from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from context import SessionContext


@asynccontextmanager
async def lifespan(app: FastAPI):
    context = SessionContext()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
