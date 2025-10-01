import json
import os
import uuid
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from api.testWorkflow import test_workflow_1_simple_login
from storage.postgres.crud import workflow
from utils import setup_logging
from workflow_builder.automaton.automaton import Automaton
from .routes import router
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

setup_logging()
app = FastAPI(lifespan=lifespan)

# Настройка CORS для веб-части
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все HTTP методы (GET, POST, OPTIONS и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

app.include_router(router)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    # uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    test_client = TestClient(app)
    global_session_id = str(uuid.uuid4())

    def save_workflow_and_test_events():
        body = {
            "states": test_workflow_1_simple_login()
        }
        response = test_client.post("/workflow/save", json=body)
        assert response.status_code == 200
        resp_json = response.json()

        events = {
            None: {},
            "submit": {"username": "abc112", "password": "12345678910"},
            "logout": {}
        }
        for event in events:
            response = test_client.post(
                "/client/workflow",
                json={
                    "client_session_id": global_session_id,
                    "client_workflow_id": resp_json["wf_description_id"],
                    "event_name": event,
                    "context": events[event],
                },
            )
        assert response.status_code == 200

    save_workflow_and_test_events()

    def test_user_session():
        client_session_id = "1234567890"
        workflow_id = "68d976ced58d8162a65994f3"
        response = test_client.post(
            "/client/workflow",
            json={
                "client_session_id": client_session_id,
                "client_workflow_id": workflow_id,
            },
        )
        assert response.status_code == 200

    # test_user_session()
