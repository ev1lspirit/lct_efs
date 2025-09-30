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

        automaton = Automaton(session_id="1234567890", workflow_id="68da5935428adff22feedeab")
        automaton.run()

        response = test_client.post("/workflow/save", json=testWorkflow.test_workflow_1_simple_login())
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
    #test_user_session()

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
                    {"variable": "cart_empty", "case": "True", "state_id": "EmptyCartScreen"},
                    {"variable": "cart_empty", "case": "False", "state_id": "CartReviewScreen"},
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
                    {"variable": "cart_updated", "case": None, "state_id": "InitCart"},
                ],
                "expressions": [
                    {
                        "variable": "cart_updated",
                        "url": "http://api.shop.com/cart/update",
                        "params": {"items": "{{updated_items}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "CheckUserAuth",
                "transitions": [
                    {"variable": "is_authenticated", "case": "True", "state_id": "ShippingAddressScreen"},
                    {"variable": "is_authenticated", "case": "False", "state_id": "GuestCheckoutScreen"},
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
                    {"variable": "address_valid", "case": "True", "state_id": "PaymentMethodScreen"},
                    {"variable": "address_valid", "case": "False", "state_id": "ShippingAddressScreen"},
                ],
                "expressions": [
                    {
                        "variable": "address_valid",
                        "url": "http://api.shipping.com/validate",
                        "params": {"address": "{{shipping_address}}"},
                        "method": "post",
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
                    {"variable": "paypal_success", "case": "True", "state_id": "OrderConfirmation"},
                    {"variable": "paypal_success", "case": "False", "state_id": "PaymentMethodScreen"},
                ],
                "expressions": [
                    {
                        "variable": "paypal_success",
                        "url": "http://api.paypal.com/checkout",
                        "params": {"amount": "{{total_amount}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "ProcessPayment",
                "transitions": [
                    {"variable": "payment_success", "case": "True", "state_id": "OrderConfirmation"},
                    {"variable": "payment_success", "case": "False", "state_id": "PaymentErrorScreen"},
                ],
                "expressions": [
                    {
                        "variable": "payment_success",
                        "url": "http://api.payment.com/process",
                        "params": {"card_data": "{{encrypted_card}}", "amount": "{{total_amount}}"},
                        "method": "post",
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


def test_workflow_3_complex_loan_application():
    """Сложный workflow для заявки на кредит с множественными проверками"""
    test_json = {
        "states": [
            {
                "state_type": "technical",
                "name": "StartApplication",
                "transitions": [
                    {"variable": "existing_customer", "case": "True", "state_id": "FetchCustomerData"},
                    {"variable": "existing_customer", "case": "False", "state_id": "PersonalInfoScreen"},
                ],
                "expressions": [
                    {
                        "variable": "existing_customer",
                        "dependent_variables": ["customer_id"],
                        "expression": "customer_id is not None",
                    }
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "FetchCustomerData",
                "transitions": [
                    {"variable": "data_fetched", "case": None, "state_id": "CheckEligibility"},
                ],
                "expressions": [
                    {
                        "variable": "data_fetched",
                        "url": "http://api.bank.com/customer/data",
                        "params": {"id": "{{customer_id}}"},
                        "method": "get",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "PersonalInfoScreen",
                "transitions": [
                    {"case": "next", "state_id": "ValidatePersonalInfo"},
                    {"case": "cancel", "state_id": "ApplicationCancelled"},
                ],
                "expressions": [
                    {"event_name": "next"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidatePersonalInfo",
                "transitions": [
                    {"variable": "info_valid", "case": "True", "state_id": "EmploymentInfoScreen"},
                    {"variable": "info_valid", "case": "False", "state_id": "PersonalInfoScreen"},
                ],
                "expressions": [
                    {
                        "variable": "info_valid",
                        "dependent_variables": ["ssn", "dob", "email"],
                        "expression": "len(ssn) == 9 and dob is not None and '@' in email",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "EmploymentInfoScreen",
                "transitions": [
                    {"case": "next", "state_id": "VerifyEmployment"},
                    {"case": "back", "state_id": "PersonalInfoScreen"},
                    {"case": "cancel", "state_id": "ApplicationCancelled"},
                ],
                "expressions": [
                    {"event_name": "next"},
                    {"event_name": "back"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "VerifyEmployment",
                "transitions": [
                    {"variable": "employment_verified", "case": "True", "state_id": "FinancialInfoScreen"},
                    {"variable": "employment_verified", "case": "False", "state_id": "ManualVerificationScreen"},
                ],
                "expressions": [
                    {
                        "variable": "employment_verified",
                        "url": "http://api.verify.com/employment",
                        "params": {"employer": "{{employer_name}}", "employee": "{{employee_data}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ManualVerificationScreen",
                "transitions": [
                    {"case": "upload_docs", "state_id": "DocumentUploadScreen"},
                    {"case": "skip", "state_id": "FinancialInfoScreen"},
                    {"case": "back", "state_id": "EmploymentInfoScreen"},
                ],
                "expressions": [
                    {"event_name": "upload_docs"},
                    {"event_name": "skip"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "DocumentUploadScreen",
                "transitions": [
                    {"case": "upload_complete", "state_id": "ProcessDocuments"},
                    {"case": "back", "state_id": "ManualVerificationScreen"},
                ],
                "expressions": [
                    {"event_name": "upload_complete"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "ProcessDocuments",
                "transitions": [
                    {"variable": "docs_processed", "case": None, "state_id": "FinancialInfoScreen"},
                ],
                "expressions": [
                    {
                        "variable": "docs_processed",
                        "url": "http://api.docprocess.com/analyze",
                        "params": {"documents": "{{uploaded_docs}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "FinancialInfoScreen",
                "transitions": [
                    {"case": "next", "state_id": "CheckEligibility"},
                    {"case": "back", "state_id": "EmploymentInfoScreen"},
                    {"case": "cancel", "state_id": "ApplicationCancelled"},
                ],
                "expressions": [
                    {"event_name": "next"},
                    {"event_name": "back"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "CheckEligibility",
                "transitions": [
                    {"variable": "credit_score_high", "case": "True", "state_id": "RunCreditCheck"},
                    {"variable": "credit_score_medium", "case": "True", "state_id": "AdditionalInfoScreen"},
                    {"variable": ["credit_score_high", "credit_score_medium"], "case": "False",
                     "state_id": "ApplicationRejected"},
                ],
                "expressions": [
                    {
                        "variable": "credit_score_high",
                        "dependent_variables": ["annual_income", "debt_ratio"],
                        "expression": "annual_income > 75000 and debt_ratio < 0.3",
                    },
                    {
                        "variable": "credit_score_medium",
                        "dependent_variables": ["annual_income", "debt_ratio"],
                        "expression": "annual_income > 50000 and debt_ratio < 0.4",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "AdditionalInfoScreen",
                "transitions": [
                    {"case": "submit", "state_id": "RunCreditCheck"},
                    {"case": "back", "state_id": "FinancialInfoScreen"},
                ],
                "expressions": [
                    {"event_name": "submit"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "RunCreditCheck",
                "transitions": [
                    {"variable": "credit_approved", "case": "True", "state_id": "CalculateLoanTerms"},
                    {"variable": "credit_approved", "case": "False", "state_id": "ManualReviewRequired"},
                ],
                "expressions": [
                    {
                        "variable": "credit_approved",
                        "url": "http://api.creditbureau.com/check",
                        "params": {"ssn": "{{ssn}}", "consent": "{{consent_token}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ManualReviewRequired",
                "transitions": [
                    {"variable": "review_complete", "case": "approved", "state_id": "CalculateLoanTerms"},
                    {"variable": "review_complete", "case": "rejected", "state_id": "ApplicationRejected"},
                    {"variable": "review_complete", "case": "pending", "state_id": "ApplicationPending"},
                ],
                "expressions": [
                    {
                        "variable": "review_complete",
                        "dependent_variables": ["manual_review_status"],
                        "expression": "manual_review_status",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "CalculateLoanTerms",
                "transitions": [
                    {"variable": "terms_calculated", "case": None, "state_id": "LoanOfferScreen"},
                ],
                "expressions": [
                    {
                        "variable": "terms_calculated",
                        "dependent_variables": ["credit_score", "income", "loan_amount"],
                        "expression": "{'rate': 3.5 + (800 - credit_score) * 0.01, 'term': 360}",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "LoanOfferScreen",
                "transitions": [
                    {"case": "accept", "state_id": "GenerateContract"},
                    {"case": "negotiate", "state_id": "NegotiationScreen"},
                    {"case": "reject", "state_id": "ApplicationWithdrawn"},
                ],
                "expressions": [
                    {"event_name": "accept"},
                    {"event_name": "negotiate"},
                    {"event_name": "reject"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "NegotiationScreen",
                "transitions": [
                    {"case": "submit_counter", "state_id": "EvaluateCounterOffer"},
                    {"case": "accept_original", "state_id": "GenerateContract"},
                    {"case": "cancel", "state_id": "ApplicationWithdrawn"},
                ],
                "expressions": [
                    {"event_name": "submit_counter"},
                    {"event_name": "accept_original"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "EvaluateCounterOffer",
                "transitions": [
                    {"variable": "counter_acceptable", "case": "True", "state_id": "GenerateContract"},
                    {"variable": "counter_acceptable", "case": "False", "state_id": "LoanOfferScreen"},
                ],
                "expressions": [
                    {
                        "variable": "counter_acceptable",
                        "dependent_variables": ["requested_rate", "min_rate"],
                        "expression": "requested_rate >= min_rate",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "GenerateContract",
                "transitions": [
                    {"variable": "contract_generated", "case": None, "state_id": "SignatureScreen"},
                ],
                "expressions": [
                    {
                        "variable": "contract_generated",
                        "url": "http://api.contracts.com/generate",
                        "params": {"loan_terms": "{{final_terms}}", "customer": "{{customer_data}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "SignatureScreen",
                "transitions": [
                    {"case": "sign", "state_id": "ProcessSignature"},
                    {"case": "review", "state_id": "ContractReviewScreen"},
                    {"case": "cancel", "state_id": "ApplicationWithdrawn"},
                ],
                "expressions": [
                    {"event_name": "sign"},
                    {"event_name": "review"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ContractReviewScreen",
                "transitions": [
                    {"case": "back", "state_id": "SignatureScreen"},
                ],
                "expressions": [
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "ProcessSignature",
                "transitions": [
                    {"variable": "signature_valid", "case": "True", "state_id": "ApplicationComplete"},
                    {"variable": "signature_valid", "case": "False", "state_id": "SignatureScreen"},
                ],
                "expressions": [
                    {
                        "variable": "signature_valid",
                        "url": "http://api.esign.com/verify",
                        "params": {"signature": "{{digital_signature}}", "contract_id": "{{contract_id}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ApplicationComplete",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
            {
                "state_type": "screen",
                "name": "ApplicationRejected",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
            {
                "state_type": "screen",
                "name": "ApplicationPending",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
            {
                "state_type": "screen",
                "name": "ApplicationWithdrawn",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
            {
                "state_type": "technical",
                "name": "ApplicationCancelled",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json


def test_workflow_4_simple_survey():
    """Простой workflow опроса пользователя"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "WelcomeScreen",
                "transitions": [
                    {"case": "start", "state_id": "Question1"},
                ],
                "expressions": [
                    {"event_name": "start"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "Question1",
                "transitions": [
                    {"case": "next", "state_id": "ValidateAnswer1"},
                ],
                "expressions": [
                    {"event_name": "next"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidateAnswer1",
                "transitions": [
                    {"variable": "answer_valid", "case": "True", "state_id": "Question2"},
                    {"variable": "answer_valid", "case": "False", "state_id": "Question1"},
                ],
                "expressions": [
                    {
                        "variable": "answer_valid",
                        "dependent_variables": ["answer1"],
                        "expression": "len(answer1) > 0",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "Question2",
                "transitions": [
                    {"case": "finish", "state_id": "ThankYouScreen"},
                ],
                "expressions": [
                    {"event_name": "finish"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ThankYouScreen",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }
    return test_json


def test_workflow_6_complex_booking():
    """Сложный workflow бронирования с множественными проверками"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "SearchScreen",
                "transitions": [
                    {"case": "search", "state_id": "ValidateSearchParams"},
                ],
                "expressions": [
                    {"event_name": "search"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidateSearchParams",
                "transitions": [
                    {"variable": "params_valid", "case": "True", "state_id": "FetchAvailability"},
                    {"variable": "params_valid", "case": "False", "state_id": "SearchScreen"},
                ],
                "expressions": [
                    {
                        "variable": "params_valid",
                        "dependent_variables": ["check_in", "check_out", "guests"],
                        "expression": "check_in < check_out and guests > 0",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "FetchAvailability",
                "transitions": [
                    {"variable": "rooms_available", "case": "True", "state_id": "ShowResults"},
                    {"variable": "rooms_available", "case": "False", "state_id": "NoResultsScreen"},
                ],
                "expressions": [
                    {
                        "variable": "rooms_available",
                        "url": "http://api.booking.com/availability",
                        "params": {"dates": "{{dates}}", "guests": "{{guests}}"},
                        "method": "get",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "NoResultsScreen",
                "transitions": [
                    {"case": "modify_search", "state_id": "SearchScreen"},
                    {"case": "exit", "state_id": "ExitFlow"},
                ],
                "expressions": [
                    {"event_name": "modify_search"},
                    {"event_name": "exit"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ShowResults",
                "transitions": [
                    {"case": "select_room", "state_id": "CheckAvailability"},
                    {"case": "modify_search", "state_id": "SearchScreen"},
                ],
                "expressions": [
                    {"event_name": "select_room"},
                    {"event_name": "modify_search"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "CheckAvailability",
                "transitions": [
                    {"variable": "still_available", "case": "True", "state_id": "GuestInfoScreen"},
                    {"variable": "still_available", "case": "False", "state_id": "UnavailableScreen"},
                ],
                "expressions": [
                    {
                        "variable": "still_available",
                        "url": "http://api.booking.com/check-room",
                        "params": {"room_id": "{{selected_room}}"},
                        "method": "get",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "UnavailableScreen",
                "transitions": [
                    {"case": "back", "state_id": "ShowResults"},
                ],
                "expressions": [
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "GuestInfoScreen",
                "transitions": [
                    {"case": "continue", "state_id": "ValidateGuestInfo"},
                    {"case": "back", "state_id": "ShowResults"},
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
                "name": "ValidateGuestInfo",
                "transitions": [
                    {"variable": "guest_info_valid", "case": "True", "state_id": "PaymentScreen"},
                    {"variable": "guest_info_valid", "case": "False", "state_id": "GuestInfoScreen"},
                ],
                "expressions": [
                    {
                        "variable": "guest_info_valid",
                        "dependent_variables": ["guest_name", "guest_email", "guest_phone"],
                        "expression": "len(guest_name) > 2 and '@' in guest_email and len(guest_phone) > 8",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "PaymentScreen",
                "transitions": [
                    {"case": "pay", "state_id": "ProcessPayment"},
                    {"case": "back", "state_id": "GuestInfoScreen"},
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
                "name": "ProcessPayment",
                "transitions": [
                    {"variable": "payment_success", "case": "True", "state_id": "CreateBooking"},
                    {"variable": "payment_success", "case": "False", "state_id": "PaymentError"},
                ],
                "expressions": [
                    {
                        "variable": "payment_success",
                        "url": "http://api.payment.com/charge",
                        "params": {"amount": "{{total_amount}}", "card": "{{card_data}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "PaymentError",
                "transitions": [
                    {"case": "retry", "state_id": "PaymentScreen"},
                    {"case": "cancel", "state_id": "ExitFlow"},
                ],
                "expressions": [
                    {"event_name": "retry"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "CreateBooking",
                "transitions": [
                    {"variable": "booking_created", "case": None, "state_id": "SendConfirmation"},
                ],
                "expressions": [
                    {
                        "variable": "booking_created",
                        "url": "http://api.booking.com/create",
                        "params": {"room": "{{selected_room}}", "guest": "{{guest_data}}",
                                   "payment": "{{payment_id}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "SendConfirmation",
                "transitions": [
                    {"variable": "confirmation_sent", "case": None, "state_id": "BookingComplete"},
                ],
                "expressions": [
                    {
                        "variable": "confirmation_sent",
                        "url": "http://api.email.com/send",
                        "params": {"to": "{{guest_email}}", "booking_id": "{{booking_id}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "BookingComplete",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
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


def test_workflow_7_document_approval():
    """Запутанный workflow согласования документа с циклическими переходами"""
    test_json = {
        "states": [
            {
                "state_type": "screen",
                "name": "UploadDocument",
                "transitions": [
                    {"case": "upload", "state_id": "ValidateDocument"},
                ],
                "expressions": [
                    {"event_name": "upload"},
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ValidateDocument",
                "transitions": [
                    {"variable": "doc_valid", "case": "True", "state_id": "AssignReviewer"},
                    {"variable": "doc_valid", "case": "False", "state_id": "UploadDocument"},
                ],
                "expressions": [
                    {
                        "variable": "doc_valid",
                        "dependent_variables": ["file_size", "file_type"],
                        "expression": "file_size < 10000000 and file_type in ['pdf', 'docx']",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "AssignReviewer",
                "transitions": [
                    {"variable": "reviewer_assigned", "case": None, "state_id": "NotifyReviewer"},
                ],
                "expressions": [
                    {
                        "variable": "reviewer_assigned",
                        "url": "http://api.workflow.com/assign",
                        "params": {"document_id": "{{doc_id}}", "department": "{{department}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "NotifyReviewer",
                "transitions": [
                    {"variable": "notification_sent", "case": None, "state_id": "WaitingForReview"},
                ],
                "expressions": [
                    {
                        "variable": "notification_sent",
                        "url": "http://api.notify.com/send",
                        "params": {"reviewer_id": "{{reviewer_id}}", "doc_id": "{{doc_id}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "WaitingForReview",
                "transitions": [
                    {"case": "reviewed", "state_id": "ProcessReview"},
                    {"case": "timeout", "state_id": "EscalateReview"},
                    {"case": "cancel", "state_id": "CancelWorkflow"},
                ],
                "expressions": [
                    {"event_name": "reviewed"},
                    {"event_name": "timeout"},
                    {"event_name": "cancel"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ProcessReview",
                "transitions": [
                    {"variable": "review_decision", "case": "approved", "state_id": "DocumentApproved"},
                    {"variable": "review_decision", "case": "rejected", "state_id": "DocumentRejected"},
                    {"variable": "review_decision", "case": "revision", "state_id": "RequestRevision"},
                ],
                "expressions": [
                    {
                        "variable": "review_decision",
                        "dependent_variables": ["decision"],
                        "expression": "decision",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "RequestRevision",
                "transitions": [
                    {"case": "revise", "state_id": "ValidateDocument"},
                    {"case": "appeal", "state_id": "EscalateReview"},
                ],
                "expressions": [
                    {"event_name": "revise"},
                    {"event_name": "appeal"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "EscalateReview",
                "transitions": [
                    {"variable": "escalated", "case": None, "state_id": "ManagerReview"},
                ],
                "expressions": [
                    {
                        "variable": "escalated",
                        "url": "http://api.workflow.com/escalate",
                        "params": {"doc_id": "{{doc_id}}", "reason": "{{escalation_reason}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ManagerReview",
                "transitions": [
                    {"case": "manager_decision", "state_id": "ProcessManagerDecision"},
                ],
                "expressions": [
                    {"event_name": "manager_decision"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ProcessManagerDecision",
                "transitions": [
                    {"variable": "manager_decision", "case": "approved", "state_id": "DocumentApproved"},
                    {"variable": "manager_decision", "case": "rejected", "state_id": "DocumentRejected"},
                    {"variable": "manager_decision", "case": "back_to_reviewer", "state_id": "AssignReviewer"},
                ],
                "expressions": [
                    {
                        "variable": "manager_decision",
                        "dependent_variables": ["manager_choice"],
                        "expression": "manager_choice",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "DocumentApproved",
                "transitions": [
                    {"variable": "approval_recorded", "case": None, "state_id": "WorkflowComplete"},
                ],
                "expressions": [
                    {
                        "variable": "approval_recorded",
                        "url": "http://api.documents.com/approve",
                        "params": {"doc_id": "{{doc_id}}", "approver": "{{approver_id}}"},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "DocumentRejected",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
            {
                "state_type": "technical",
                "name": "CancelWorkflow",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
            {
                "state_type": "screen",
                "name": "WorkflowComplete",
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
