import logging
import uuid
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from api.testWorkflow import *
from utils import setup_logging
from .routes import router

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


logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    test_client = TestClient(app)
    global_session_id = str(uuid.uuid4())

    def generate_test_scenarios_ecommerce_checkout():
        scenarios = {}

        # Scenario 1: Empty Cart Path
        scenarios["empty_cart"] = {
            "description": "User with empty cart",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "cart_items": [],
                        "user_token": "user123"
                    }
                },
                {
                    "event_name": "continue_shopping",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        }

        # Scenario 2: Happy Path - Authenticated User, Credit Card Success
        scenarios["happy_path_authenticated_credit_card"] = {
            "description": "Authenticated user completes checkout with credit card",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "cart_items": [{"id": 1, "name": "Product A", "price": 29.99}],
                        "user_token": "user123"
                    }
                },
                {
                    "event_name": "proceed",
                    "context": {}
                },
                {
                    "event_name": "next",
                    "context": {
                        "shipping_address": "123 Main St, City, Country"
                    }
                },
                # ValidateAddress integration would set address_valid=True automatically
                {
                    "event_name": "credit_card",
                    "context": {}
                },
                {
                    "event_name": "pay",
                    "context": {
                        "encrypted_card": "encrypted_card_data_123",
                        "total_amount": 29.99
                    }
                },
                # ProcessPayment integration would set payment_success=True automatically
                {
                    "event_name": "done",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        }

        # Scenario 3: Guest Checkout Path
        scenarios["guest_checkout"] = {
            "description": "Guest user completes checkout",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "cart_items": [{"id": 1, "name": "Product B", "price": 49.99}]
                        # No user_token - indicates guest
                    }
                },
                {
                    "event_name": "proceed",
                    "context": {
                        "user_token": "x"
                    }
                },
                {
                    "event_name": "continue_guest",
                    "context": {}
                },
                {
                    "event_name": "next",
                    "context": {
                        "shipping_address": "456 Oak St, City, Country"
                    }
                },
                {
                    "event_name": "credit_card",
                    "context": {}
                },
                {
                    "event_name": "pay",
                    "context": {
                        "encrypted_card": "encrypted_card_data_456",
                        "total_amount": 49.99
                    }
                },
                {
                    "event_name": "done",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        }

        # Scenario 4: Payment Failure and Retry Loop
        scenarios["payment_retry_loop"] = {
            "description": "User experiences payment failure and retries",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "cart_items": [{"id": 1, "name": "Product C", "price": 19.99}],
                        "user_token": "user456"
                    }
                },
                {
                    "event_name": "proceed",
                    "context": {}
                },
                {
                    "event_name": "next",
                    "context": {
                        "shipping_address": "789 Pine St, City, Country"
                    }
                },
                {
                    "event_name": "credit_card",
                    "context": {}
                },
                {
                    "event_name": "pay",
                    "context": {
                        "encrypted_card": "encrypted_card_data_789",
                        "total_amount": 19.99
                    }
                },
                # ProcessPayment integration would set payment_success=False automatically
                {
                    "event_name": "retry",
                    "context": {
                        "encrypted_card": "encrypted_card_data_789_updated"
                    }
                },
                # ProcessPayment integration would set payment_success=True on retry
                {
                    "event_name": "done",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        }

        # Scenario 5: Cart Update Loop
        scenarios["cart_update_loop"] = {
            "description": "User updates cart multiple times before checkout",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "cart_items": [{"id": 1, "name": "Product A", "price": 29.99}],
                        "user_token": "user789"
                    }
                },
                {
                    "event_name": "update_cart",
                    "context": {
                        "updated_items": [{"id": 1, "name": "Product A", "price": 29.99, "quantity": 2}]
                    }
                },
                # UpdateCart integration would set cart_updated=True automatically
                # Returns to InitCart, then back to CartReviewScreen
                {
                    "event_name": "update_cart",
                    "context": {
                        "updated_items": [{"id": 1, "name": "Product A", "price": 29.99, "quantity": 1}]
                    }
                },
                {
                    "event_name": "proceed",
                    "context": {}
                },
                {
                    "event_name": "next",
                    "context": {
                        "shipping_address": "321 Elm St, City, Country"
                    }
                },
                {
                    "event_name": "credit_card",
                    "context": {}
                },
                {
                    "event_name": "pay",
                    "context": {
                        "encrypted_card": "encrypted_card_data_321",
                        "total_amount": 29.99
                    }
                },
                {
                    "event_name": "done",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        }

        # Scenario 6: Login Flow Integration
        scenarios["login_integration"] = {
            "description": "Guest user decides to login during checkout",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "cart_items": [{"id": 1, "name": "Product D", "price": 39.99}]
                        # No user_token - indicates guest
                    }
                },
                {
                    "event_name": "proceed",
                    "context": {}
                },
                {
                    "event_name": "login",
                    "context": {
                        "username": "testuser",
                        "password": "testpass123"
                    }
                },
                {
                    "event_name": "login_success",
                    "context": {
                        "user_token": "newly_generated_token_123"
                    }
                },
                {
                    "event_name": "next",
                    "context": {
                        "shipping_address": "654 Maple St, City, Country"
                    }
                },
                {
                    "event_name": "credit_card",
                    "context": {}
                },
                {
                    "event_name": "pay",
                    "context": {
                        "encrypted_card": "encrypted_card_data_654",
                        "total_amount": 39.99
                    }
                },
                {
                    "event_name": "done",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        }

        # Scenario 7: PayPal Alternative Payment
        scenarios["paypal_payment"] = {
            "description": "User chooses PayPal payment method",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "cart_items": [{"id": 1, "name": "Product E", "price": 59.99}],
                        "user_token": "user_paypal"
                    }
                },
                {
                    "event_name": "proceed",
                    "context": {}
                },
                {
                    "event_name": "next",
                    "context": {
                        "shipping_address": "987 Birch St, City, Country"
                    }
                },
                {
                    "event_name": "paypal",
                    "context": {
                        "total_amount": 59.99
                    }
                },
                # PayPalFlow integration would set paypal_success=True automatically
                {
                    "event_name": "done",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        }

        # Scenario 8: Navigation Back Loops
        scenarios["navigation_back_loops"] = {
            "description": "User navigates back through multiple screens",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "cart_items": [{"id": 1, "name": "Product F", "price": 25.99}],
                        "user_token": "user_back_nav"
                    }
                },
                {
                    "event_name": "proceed",
                    "context": {}
                },
                {
                    "event_name": "back",  # From ShippingAddressScreen back to CartReviewScreen
                    "context": {}
                },
                {
                    "event_name": "proceed",
                    "context": {}
                },
                {
                    "event_name": "next",
                    "context": {
                        "shipping_address": "147 Cedar St, City, Country"
                    }
                },
                {
                    "event_name": "credit_card",
                    "context": {}
                },
                {
                    "event_name": "back",  # From CardPaymentScreen back to PaymentMethodScreen
                    "context": {}
                },
                {
                    "event_name": "paypal",
                    "context": {
                        "total_amount": 25.99
                    }
                },
                {
                    "event_name": "done",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        }

        return scenarios

    def run_workflow_scenario(test_client, workflow_id, scenario_name, scenario_data):
        """Execute a workflow scenario and return the results"""

        session_id = str(uuid.uuid4())
        results = {
            "scenario": scenario_name,
            "description": scenario_data["description"],
            "session_id": session_id,
            "responses": [],
            "final_state_reached": False
        }

        logger.info(f"Starting scenario: {scenario_name} - {scenario_data['description']}")

        try:
            for event_data in scenario_data["events"]:
                response = test_client.post(
                    "/client/workflow",
                    json={
                        "client_session_id": session_id,
                        "client_workflow_id": workflow_id,
                        "event_name": event_data["event_name"],
                        "context": event_data["context"],
                    },
                )

                assert response.status_code == 200, f"Expected 200, got {response.status_code}"

                resp_json = response.json()
                results["responses"].append({
                    "event": event_data["event_name"],
                    "response": resp_json
                })

                # Check if we reached the final state
                if (event_data["event_name"] == "done" or
                    event_data["event_name"] == "continue_shopping"):
                    results["final_state_reached"] = True
                    logger.info(f"Final state reached for scenario: {scenario_name}")

        except Exception as e:
            logger.error(f"Scenario {scenario_name} failed: {str(e)}")
            results["error"] = str(e)

        return results

    def test_individual_scenario(test_client, scenario_name):
        """Test individual workflow scenarios"""

        workflow_json = test_workflow_2_ecommerce_checkout()
        save_response = test_client.post(
            "/workflow/save",
            json={
                "states": workflow_json,
                "predefined_context": {
                    "default_currency": "USD",
                    "max_retry_attempts": 3
                }
            }
        )

        assert save_response.status_code == 200
        workflow_id = save_response.json()["wf_description_id"]

        scenarios = generate_test_scenarios_ecommerce_checkout()
        scenario_data = scenarios[scenario_name]

        result = run_workflow_scenario(test_client, workflow_id, scenario_name, scenario_data)

        # assert result["final_state_reached"], f"Scenario {scenario_name} failed to reach final state"
        assert "error" not in result, f"Scenario {scenario_name} had error: {result['error']}"

    test_individual_scenario(test_client, "guest_checkout")
