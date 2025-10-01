from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient

from workflow_builder.automaton.automaton import Automaton
from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    # uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    test_client = TestClient(app)

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
                        {
                            "variable": "data_fetched",
                            "case": None,
                            "state_id": "ProcessData",
                        },
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
        return test_json

def test_workflow_1_simple_login():
    """Простой workflow авторизации пользователя"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "LoginScreen",
                "transitions": [
                    {"case": "submit", "state_id": "ValidateCredentials"},
                    {"case": "forgot_password", "state_id": "ForgotPasswordScreen"},
                ],
                "expressions": [
                    {"event_name": "submit"},
                    {"event_name": "forgot_password"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidateCredentials",
                "transitions": [
                    {"variable": "is_valid", "case": "True", "state_id": "FetchUserProfile"},
                    {"variable": "is_valid", "case": "False", "state_id": "LoginScreen"},
                ],
                "expressions": [
                    {
                        "variable": "is_valid",
                        "dependent_variables": ["username", "password"],
                        "expression": "len(username) > 0 and len(password) >= 8",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "FetchUserProfile",
                "transitions": [
                    {"variable": "profile_loaded", "case": None, "state_id": "DashboardScreen"},
                ],
                "expressions": [
                    {
                        "variable": "profile_loaded",
                        "url": "http://localhost:8080",
                        "params": {},
                        "method": "get",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "DashboardScreen",
                "transitions": [
                    {"case": "logout", "state_id": "LogoutState"},
                ],
                "expressions": [
                    {"event_name": "logout"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ForgotPasswordScreen",
                "transitions": [
                    {"case": "back", "state_id": "LoginScreen"},
                    {"case": "reset", "state_id": "LogoutState"},
                ],
                "expressions": [
                    {"event_name": "back"},
                    {"event_name": "reset"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "LogoutState",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json

def test_workflow_2_ecommerce_checkout():
    """Средней сложности workflow для процесса оформления заказа в e-commerce"""
    test_json = {
        "states": [
            {
                "state_type": "technical",
                "name": "InitCart",
                "transitions": [
                    {
                        "variable": "cart_empty",
                        "case": "True",
                        "state_id": "EmptyCartScreen",
                    },
                    {
                        "variable": "cart_empty",
                        "case": "False",
                        "state_id": "CartReviewScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "cart_empty",
                        "dependent_variables": ["cart_items"],
                        "expression": "len(cart_items) == 0",
                    }
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "EmptyCartScreen",
                "transitions": [
                    {"case": "continue_shopping", "state_id": "ExitFlow"},
                ],
                "expressions": [
                    {"event_name": "continue_shopping"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "CartReviewScreen",
                "transitions": [
                    {"case": "proceed", "state_id": "CheckUserAuth"},
                    {"case": "update_cart", "state_id": "UpdateCart"},
                    {"case": "cancel", "state_id": "ExitFlow"},
                ],
                "expressions": [
                    {"event_name": "proceed"},
                    {"event_name": "update_cart"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "UpdateCart",
                "transitions": [
                    {
                        "variable": "cart_updated",
                        "case": None,
                        "state_id": "CheckCartUpdate",
                    },  # Single transition to technical state
                ],
                "expressions": [
                    {
                        "variable": "cart_updated",
                        "url": "http://localhost:8080",
                        "params": {},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",  # New technical state to handle cart update result
                "name": "CheckCartUpdate",
                "transitions": [
                    {
                        "variable": "cart_updated",
                        "case": "True",
                        "state_id": "InitCart",
                    },
                    {
                        "variable": "cart_updated",
                        "case": "False",
                        "state_id": "CartReviewScreen",
                    },  # Handle failure case
                ],
                "expressions": [
                    {
                        "variable": "cart_updated",
                        "dependent_variables": ["cart_updated"],
                        "expression": "cart_updated is True",  # This will evaluate the API response
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "CheckUserAuth",
                "transitions": [
                    {
                        "variable": "is_authenticated",
                        "case": "True",
                        "state_id": "ShippingAddressScreen",
                    },
                    {
                        "variable": "is_authenticated",
                        "case": "False",
                        "state_id": "GuestCheckoutScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "is_authenticated",
                        "dependent_variables": ["user_token"],
                        "expression": "user_token is not None and len(user_token) > 0",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "GuestCheckoutScreen",
                "transitions": [
                    {"case": "continue_guest", "state_id": "ShippingAddressScreen"},
                    {"case": "login", "state_id": "LoginFlowScreen"},
                    {"case": "back", "state_id": "CartReviewScreen"},
                ],
                "expressions": [
                    {"event_name": "continue_guest"},
                    {"event_name": "login"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "LoginFlowScreen",
                "transitions": [
                    {"case": "login_success", "state_id": "ShippingAddressScreen"},
                    {"case": "cancel", "state_id": "GuestCheckoutScreen"},
                ],
                "expressions": [
                    {"event_name": "login_success"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ShippingAddressScreen",
                "transitions": [
                    {"case": "next", "state_id": "ValidateAddress"},
                    {"case": "back", "state_id": "CartReviewScreen"},
                ],
                "expressions": [
                    {"event_name": "next"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "ValidateAddress",
                "transitions": [
                    {
                        "variable": "address_valid",
                        "case": None,
                        "state_id": "CheckAddressValidation",
                    },  # Single transition to technical state
                ],
                "expressions": [
                    {
                        "variable": "address_valid",
                        "url": "http://localhost:8000",
                        "params": {"address": "{{shipping_address}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",  # New technical state to handle address validation result
                "name": "CheckAddressValidation",
                "transitions": [
                    {
                        "variable": "address_valid",
                        "case": "True",
                        "state_id": "PaymentMethodScreen",
                    },
                    {
                        "variable": "address_valid",
                        "case": "False",
                        "state_id": "ShippingAddressScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "address_valid",
                        "dependent_variables": ["address_valid"],
                        "expression": "address_valid is True",  # This will evaluate the API response
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "PaymentMethodScreen",
                "transitions": [
                    {"case": "credit_card", "state_id": "CardPaymentScreen"},
                    {"case": "paypal", "state_id": "PayPalFlow"},
                    {"case": "back", "state_id": "ShippingAddressScreen"},
                ],
                "expressions": [
                    {"event_name": "credit_card"},
                    {"event_name": "paypal"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "CardPaymentScreen",
                "transitions": [
                    {"case": "pay", "state_id": "ProcessPayment"},
                    {"case": "back", "state_id": "PaymentMethodScreen"},
                ],
                "expressions": [
                    {"event_name": "pay"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "PayPalFlow",
                "transitions": [
                    {
                        "variable": "paypal_success",
                        "case": None,
                        "state_id": "CheckPayPalResult",
                    },  # Single transition to technical state
                ],
                "expressions": [
                    {
                        "variable": "paypal_success",
                        "url": "http://localhost:8000",
                        "params": {},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",  # New technical state to handle PayPal result
                "name": "CheckPayPalResult",
                "transitions": [
                    {
                        "variable": "paypal_success",
                        "case": "True",
                        "state_id": "OrderConfirmation",
                    },
                    {
                        "variable": "paypal_success",
                        "case": "False",
                        "state_id": "PaymentMethodScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "paypal_success",
                        "dependent_variables": ["paypal_success"],
                        "expression": "paypal_success is True",  # This will evaluate the API response
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "ProcessPayment",
                "transitions": [
                    {
                        "case": None,
                        "state_id": "CheckPaymentResult",
                        "variable": "payment_success",
                    },  # Single transition to technical state
                ],
                "expressions": [
                    {
                        "variable": "payment_success",
                        "url": "http://localhost:8000",
                        "params": {},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",  # New technical state to handle payment result
                "name": "CheckPaymentResult",
                "transitions": [
                    {
                        "variable": "payment_success",
                        "case": "True",
                        "state_id": "OrderConfirmation",
                    },
                    {
                        "variable": "payment_success",
                        "case": "False",
                        "state_id": "PaymentErrorScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "payment_success",
                        "dependent_variables": ["payment_success"],
                        "expression": "payment_success is True",  # This will evaluate the API response
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "PaymentErrorScreen",
                "transitions": [
                    {"case": "retry", "state_id": "CardPaymentScreen"},
                    {"case": "change_method", "state_id": "PaymentMethodScreen"},
                    {"case": "cancel", "state_id": "ExitFlow"},
                ],
                "expressions": [
                    {"event_name": "retry"},
                    {"event_name": "change_method"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "OrderConfirmation",
                "transitions": [
                    {"case": "done", "state_id": "ExitFlow"},
                ],
                "expressions": [
                    {"event_name": "done"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ExitFlow",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json

def test_workflow_8_extreme_complexity():
    """Максимально сложный и запутанный workflow с множественными циклами"""
    test_json = {
        "states": [
            {
                "state_type": "technical",
                "name": "SystemInit",
                "transitions": [
                    {"variable": "system_ready", "case": "True", "state_id": "UserAuthentication"},
                    {"variable": "system_ready", "case": "False", "state_id": "MaintenanceMode"},
                ],
                "expressions": [
                    {
                        "variable": "system_ready",
                        "dependent_variables": ["system_status"],
                        "expression": "system_status == 'operational'",
                    }
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "MaintenanceMode",
                "transitions": [
                    {"case": "retry", "state_id": "SystemInit"},
                ],
                "expressions": [
                    {"event_name": "retry"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "UserAuthentication",
                "transitions": [
                    {"case": "login", "state_id": "ValidateCredentials"},
                    {"case": "guest", "state_id": "GuestAccess"},
                    {"case": "register", "state_id": "Registration"},
                ],
                "expressions": [
                    {"event_name": "login"},
                    {"event_name": "guest"},
                    {"event_name": "register"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "ValidateCredentials",
                "transitions": [
                    {"variable": "auth_result", "case": "success", "state_id": "CheckUserRole"},
                    {"variable": "auth_result", "case": "failed", "state_id": "AuthenticationFailed"},
                    {"variable": "auth_result", "case": "locked", "state_id": "AccountLocked"},
                ],
                "expressions": [
                    {
                        "variable": "auth_result",
                        "url": "http://api.auth.com/validate",
                        "params": {"username": "{{username}}", "password": "{{password}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "AuthenticationFailed",
                "transitions": [
                    {"case": "retry", "state_id": "UserAuthentication"},
                    {"case": "forgot", "state_id": "PasswordReset"},
                ],
                "expressions": [
                    {"event_name": "retry"},
                    {"event_name": "forgot"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "AccountLocked",
                "transitions": [
                    {"case": "unlock_request", "state_id": "UnlockProcess"},
                    {"case": "back", "state_id": "UserAuthentication"},
                ],
                "expressions": [
                    {"event_name": "unlock_request"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "UnlockProcess",
                "transitions": [
                    {"variable": "unlock_status", "case": None, "state_id": "UserAuthentication"},
                ],
                "expressions": [
                    {
                        "variable": "unlock_status",
                        "url": "http://api.auth.com/unlock",
                        "params": {"user_id": "{{user_id}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "PasswordReset",
                "transitions": [
                    {"variable": "reset_sent", "case": None, "state_id": "ResetSent"},
                ],
                "expressions": [
                    {
                        "variable": "reset_sent",
                        "url": "http://api.auth.com/reset",
                        "params": {"email": "{{email}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ResetSent",
                "transitions": [
                    {"case": "back", "state_id": "UserAuthentication"},
                ],
                "expressions": [
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "Registration",
                "transitions": [
                    {"case": "submit", "state_id": "ValidateRegistration"},
                    {"case": "back", "state_id": "UserAuthentication"},
                ],
                "expressions": [
                    {"event_name": "submit"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidateRegistration",
                "transitions": [
                    {"variable": "registration_valid", "case": "True", "state_id": "CreateAccount"},
                    {"variable": "registration_valid", "case": "False", "state_id": "Registration"},
                ],
                "expressions": [
                    {
                        "variable": "registration_valid",
                        "dependent_variables": ["email", "password", "terms_accepted"],
                        "expression": "'@' in email and len(password) >= 8 and terms_accepted == True",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "CreateAccount",
                "transitions": [
                    {"variable": "account_created", "case": "True", "state_id": "EmailVerification"},
                    {"variable": "account_created", "case": "False", "state_id": "Registration"},
                ],
                "expressions": [
                    {
                        "variable": "account_created",
                        "url": "http://api.users.com/create",
                        "params": {"email": "{{email}}", "password": "{{password}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "EmailVerification",
                "transitions": [
                    {"variable": "verification_sent", "case": None, "state_id": "VerificationPending"},
                ],
                "expressions": [
                    {
                        "variable": "verification_sent",
                        "url": "http://api.email.com/verify",
                        "params": {"email": "{{email}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "VerificationPending",
                "transitions": [
                    {"case": "verified", "state_id": "UserAuthentication"},
                    {"case": "resend", "state_id": "EmailVerification"},
                ],
                "expressions": [
                    {"event_name": "verified"},
                    {"event_name": "resend"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "CheckUserRole",
                "transitions": [
                    {"variable": "user_role", "case": "admin", "state_id": "AdminDashboard"},
                    {"variable": "user_role", "case": "manager", "state_id": "ManagerDashboard"},
                    {"variable": "user_role", "case": "user", "state_id": "UserDashboard"},
                ],
                "expressions": [
                    {
                        "variable": "user_role",
                        "dependent_variables": ["role"],
                        "expression": "role",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "GuestAccess",
                "transitions": [
                    {"variable": "guest_allowed", "case": "True", "state_id": "GuestDashboard"},
                    {"variable": "guest_allowed", "case": "False", "state_id": "UserAuthentication"},
                ],
                "expressions": [
                    {
                        "variable": "guest_allowed",
                        "dependent_variables": ["guest_mode_enabled"],
                        "expression": "guest_mode_enabled == True",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "AdminDashboard",
                "transitions": [
                    {"case": "user_management", "state_id": "UserManagement"},
                    {"case": "system_settings", "state_id": "SystemSettings"},
                    {"case": "logout", "state_id": "LogoutProcess"},
                ],
                "expressions": [
                    {"event_name": "user_management"},
                    {"event_name": "system_settings"},
                    {"event_name": "logout"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ManagerDashboard",
                "transitions": [
                    {"case": "team_management", "state_id": "TeamManagement"},
                    {"case": "reports", "state_id": "ReportsSection"},
                    {"case": "logout", "state_id": "LogoutProcess"},
                ],
                "expressions": [
                    {"event_name": "team_management"},
                    {"event_name": "reports"},
                    {"event_name": "logout"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "UserDashboard",
                "transitions": [
                    {"case": "profile", "state_id": "UserProfile"},
                    {"case": "logout", "state_id": "LogoutProcess"},
                ],
                "expressions": [
                    {"event_name": "profile"},
                    {"event_name": "logout"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "GuestDashboard",
                "transitions": [
                    {"case": "register", "state_id": "Registration"},
                    {"case": "exit", "state_id": "SystemExit"},
                ],
                "expressions": [
                    {"event_name": "register"},
                    {"event_name": "exit"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "UserManagement",
                "transitions": [
                    {"case": "back", "state_id": "AdminDashboard"},
                ],
                "expressions": [
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "SystemSettings",
                "transitions": [
                    {"case": "back", "state_id": "AdminDashboard"},
                ],
                "expressions": [
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "TeamManagement",
                "transitions": [
                    {"case": "back", "state_id": "ManagerDashboard"},
                ],
                "expressions": [
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ReportsSection",
                "transitions": [
                    {"case": "back", "state_id": "ManagerDashboard"},
                ],
                "expressions": [
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "UserProfile",
                "transitions": [
                    {"case": "back", "state_id": "UserDashboard"},
                ],
                "expressions": [
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "LogoutProcess",
                "transitions": [
                    {"variable": "logout_complete", "case": None, "state_id": "SystemExit"},
                ],
                "expressions": [
                    {
                        "variable": "logout_complete",
                        "url": "http://api.auth.com/logout",
                        "params": {"session_id": "{{session_id}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "SystemExit",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json


def test_workflow_9_basic_calculator():
    """Базовый workflow калькулятора"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "InputNumbers",
                "transitions": [
                    {"case": "calculate", "state_id": "ProcessCalculation"},
                ],
                "expressions": [
                    {"event_name": "calculate"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ProcessCalculation",
                "transitions": [
                    {"variable": "operation_valid", "case": "True", "state_id": "ShowResult"},
                    {"variable": "operation_valid", "case": "False", "state_id": "ErrorScreen"},
                ],
                "expressions": [
                    {
                        "variable": "operation_valid",
                        "dependent_variables": ["number1", "number2", "operation"],
                        "expression": "operation in ['+', '-', '*', '/'] and (operation != '/' or number2 != 0)",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ShowResult",
                "transitions": [
                    {"case": "new_calculation", "state_id": "InputNumbers"},
                    {"case": "exit", "state_id": "ExitCalculator"},
                ],
                "expressions": [
                    {"event_name": "new_calculation"},
                    {"event_name": "exit"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ErrorScreen",
                "transitions": [
                    {"case": "retry", "state_id": "InputNumbers"},
                ],
                "expressions": [
                    {"event_name": "retry"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ExitCalculator",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json


def test_workflow_10_simple_weather():
    """Простой workflow получения погоды"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "LocationInput",
                "transitions": [
                    {"case": "get_weather", "state_id": "ValidateLocation"},
                ],
                "expressions": [
                    {"event_name": "get_weather"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidateLocation",
                "transitions": [
                    {"variable": "location_valid", "case": "True", "state_id": "FetchWeather"},
                    {"variable": "location_valid", "case": "False", "state_id": "LocationInput"},
                ],
                "expressions": [
                    {
                        "variable": "location_valid",
                        "dependent_variables": ["city"],
                        "expression": "len(city) > 0",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "FetchWeather",
                "transitions": [
                    {"variable": "weather_data", "case": None, "state_id": "DisplayWeather"},
                ],
                "expressions": [
                    {
                        "variable": "weather_data",
                        "url": "http://api.weather.com/current",
                        "params": {"city": "{{city}}"},
                        "method": "get",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "DisplayWeather",
                "transitions": [
                    {"case": "check_another", "state_id": "LocationInput"},
                    {"case": "exit", "state_id": "ExitWeather"},
                ],
                "expressions": [
                    {"event_name": "check_another"},
                    {"event_name": "exit"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ExitWeather",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json


def test_workflow_11_basic_quiz():
    """Базовый workflow викторины"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "StartQuiz",
                "transitions": [
                    {"case": "begin", "state_id": "QuestionOne"},
                ],
                "expressions": [
                    {"event_name": "begin"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "QuestionOne",
                "transitions": [
                    {"case": "answer", "state_id": "CheckAnswer"},
                ],
                "expressions": [
                    {"event_name": "answer"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "CheckAnswer",
                "transitions": [
                    {"variable": "answer_correct", "case": "True", "state_id": "CorrectAnswer"},
                    {"variable": "answer_correct", "case": "False", "state_id": "WrongAnswer"},
                ],
                "expressions": [
                    {
                        "variable": "answer_correct",
                        "dependent_variables": ["user_answer"],
                        "expression": "user_answer == 'B'",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "CorrectAnswer",
                "transitions": [
                    {"case": "continue", "state_id": "QuizComplete"},
                ],
                "expressions": [
                    {"event_name": "continue"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "WrongAnswer",
                "transitions": [
                    {"case": "try_again", "state_id": "QuestionOne"},
                    {"case": "finish", "state_id": "QuizComplete"},
                ],
                "expressions": [
                    {"event_name": "try_again"},
                    {"event_name": "finish"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "QuizComplete",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json


def test_workflow_12_simple_contact_form():
    """Простой workflow контактной формы"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "ContactForm",
                "transitions": [
                    {"case": "submit", "state_id": "ValidateForm"},
                ],
                "expressions": [
                    {"event_name": "submit"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidateForm",
                "transitions": [
                    {"variable": "form_valid", "case": "True", "state_id": "SendMessage"},
                    {"variable": "form_valid", "case": "False", "state_id": "ContactForm"},
                ],
                "expressions": [
                    {
                        "variable": "form_valid",
                        "dependent_variables": ["name", "email", "message"],
                        "expression": "len(name) > 0 and '@' in email and len(message) > 10",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "SendMessage",
                "transitions": [
                    {"variable": "message_sent", "case": None, "state_id": "ThankYou"},
                ],
                "expressions": [
                    {
                        "variable": "message_sent",
                        "url": "http://api.contact.com/send",
                        "params": {"name": "{{name}}", "email": "{{email}}", "message": "{{message}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ThankYou",
                "transitions": [
                    {"case": "send_another", "state_id": "ContactForm"},
                    {"case": "close", "state_id": "ExitForm"},
                ],
                "expressions": [
                    {"event_name": "send_another"},
                    {"event_name": "close"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ExitForm",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json


def test_workflow_13_basic_file_upload():
    """Базовый workflow загрузки файла"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "SelectFile",
                "transitions": [
                    {"case": "upload", "state_id": "ValidateFile"},
                ],
                "expressions": [
                    {"event_name": "upload"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidateFile",
                "transitions": [
                    {"variable": "file_valid", "case": "True", "state_id": "ProcessUpload"},
                    {"variable": "file_valid", "case": "False", "state_id": "SelectFile"},
                ],
                "expressions": [
                    {
                        "variable": "file_valid",
                        "dependent_variables": ["file_size", "file_extension"],
                        "expression": "file_size < 5000000 and file_extension in ['jpg', 'png', 'pdf']",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "ProcessUpload",
                "transitions": [
                    {"variable": "upload_result", "case": None, "state_id": "UploadComplete"},
                ],
                "expressions": [
                    {
                        "variable": "upload_result",
                        "url": "http://api.storage.com/upload",
                        "params": {"file": "{{file_data}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "UploadComplete",
                "transitions": [
                    {"case": "upload_another", "state_id": "SelectFile"},
                    {"case": "done", "state_id": "ExitUpload"},
                ],
                "expressions": [
                    {"event_name": "upload_another"},
                    {"event_name": "done"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ExitUpload",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json
