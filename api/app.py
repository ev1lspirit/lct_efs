import json
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient

from storage.postgres.crud import workflow
from workflow_builder.automaton.automaton import Automaton
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
    test_client = TestClient(app)

    def test_workflow():
        test_json = {
            "states": [
                {
                    "state_type": "technical",
                    "name": "Init",
                    "transitions": [
                        {
                            "variable": "data_loaded",
                            "case": "True",
                            "state_id": "FetchData",
                        },
                        {
                            "variable": "data_loaded",
                            "case": "False",
                            "state_id": "ErrorState",
                        },
                    ],
                    "expressions": [
                        {
                            "variable": "data_loaded",
                            "dependent_variables": [],
                            "expression": "True",
                        }
                    ],
                    "initial_state": True,
                    "final_state": False,
                },
                {
                    "state_type": "integration",
                    "name": "FetchData",
                    "transitions": [
                        {"variable": "data_fetched", "case": None, "state_id": "ProcessData"},
                    ],
                    "expressions": [
                        {
                            "variable": "data_fetched",
                            "url": "http://localhost:8080",
                            "params": {},
                            "method": "get",
                        }
                    ],
                    "initial_state": False,
                    "final_state": False
                },
                {
                    "state_type": "technical",
                    "name": "ProcessData",
                    "transitions": [
                        {
                            "variable": "is_type_a",
                            "case": "True",
                            "state_id": "ShowScreenA",
                        },
                        {
                            "variable": "is_type_b",
                            "case": "True",
                            "state_id": "ShowScreenB",
                        },
                        {
                            "variable": ["is_type_a", "is_type_b"],
                            "case": "False",
                            "state_id": "ErrorState",
                        },
                    ],
                    "expressions": [
                        {
                            "variable": "is_type_a",
                            "dependent_variables": ["records"],
                            "expression": "records['type'] == 'A'",
                        },
                        {
                            "variable": "is_type_b",
                            "dependent_variables": ["records"],
                            "expression": "records['type'] == 'B'",
                        },
                    ],
                    "initial_state": False,
                    "final_state": False,
                },
                {
                    "state_type": "screen",
                    "name": "ShowScreenA",
                    "transitions": [
                        {"case": "continue", "state_id": "Final"},
                        {"case": "back", "state_id": "ProcessData"},
                    ],
                    "expressions": [
                        {"event_name": "continue"},
                        {"event_name": "back"},
                    ],
                    "initial_state": False,
                    "final_state": False,
                },
                {
                    "state_type": "screen",
                    "name": "ShowScreenB",
                    "transitions": [
                        {"case": "continue", "state_id": "Final"},
                        {"case": "back", "state_id": "ProcessData"},
                    ],
                    "expressions": [
                        {"event_name": "continue"},
                        {"event_name": "back"},
                    ],
                    "initial_state": False,
                    "final_state": False,
                },
                {
                    "state_type": "technical",
                    "name": "Final",
                    "transitions": [],
                    "expressions": [],
                    "initial_state": False,
                    "final_state": True,
                },
                {
                    "state_type": "technical",
                    "name": "ErrorState",
                    "transitions": [],
                    "expressions": [],
                    "initial_state": False,
                    "final_state": True,
                },
            ]
        }
        # import timeit
        # import psutil

        # start_time = timeit.default_timer()
        # process = psutil.Process(os.getpid())
        # start_memory = process.memory_info().rss / 1024
        # automaton = Automaton(session_id="12345678901", workflow_id="68da5935428adff22feedeab")
        # end_memory = process.memory_info().rss / 1024
        # end_time = timeit.default_timer()
        # memory_usage = end_memory - start_memory

        # creation_time = end_time - start_time
        # print(f"Creation of Automaton took {creation_time:.2f} seconds")
        # print(f"Creation of Automaton used {memory_usage:.2f} KB of memory")
        # automaton.run()

        wf_description_id = "68dbb045bb789931d1911ef5"

        # body = {"states": test_json, "predefined_context": {"records": {"type": "A"}}}
        # response = test_client.post("/workflow/save", json=body)
        # assert response.status_code == 200
        # resp_json = response.json()
        response = test_client.post(
            "/client/workflow",
            json={
                "client_session_id": "01234567890",
                "client_workflow_id": wf_description_id,
            },
        )
        assert response.status_code == 200

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

    test_workflow()
    # test_user_session()
