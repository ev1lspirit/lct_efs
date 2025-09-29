import json
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient

from workflow_builder.automaton.automaton import Automaton
from workflow_builder.state_parser.parser import GlobalStateParser
from .routes import router
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    # uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    pass