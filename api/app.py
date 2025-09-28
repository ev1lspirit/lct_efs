import json
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
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
                            "state_id": "ProcessData",
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
        response = test_client.post("/workflow/save", json=test_json["states"])
        assert response.status_code == 200

    test_workflow()
