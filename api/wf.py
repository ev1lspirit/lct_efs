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
                    "dependent_variables": [
                        "cart_items"
                    ],
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
                {
                    "case": "continue_shopping",
                    "state_id": "ExitFlow"
                },
            ],
            "expressions": [
                {
                    "event_name": "continue_shopping"
                },
            ],
            "initial_state": False,
            "final_state": False,
        },
        {
            "state_type": "screen",
            "name": "CartReviewScreen",
            "transitions": [
                {
                    "case": "proceed",
                    "state_id": "CheckUserAuth"
                },
                {
                    "case": "update_cart",
                    "state_id": "UpdateCart"
                },
                {
                    "case": "cancel",
                    "state_id": "ExitFlow"
                },
            ],
            "expressions": [
                {
                    "event_name": "proceed"
                },
                {
                    "event_name": "update_cart"
                },
                {
                    "event_name": "cancel"
                },
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
                    "method": "get",
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
                    "dependent_variables": [
                        "cart_updated"
                    ],
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
                    "dependent_variables": [
                        "user_token"
                    ],
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
                {
                    "case": "continue_guest",
                    "state_id": "ShippingAddressScreen"
                },
                {
                    "case": "login",
                    "state_id": "LoginFlowScreen"
                },
                {
                    "case": "back",
                    "state_id": "CartReviewScreen"
                },
            ],
            "expressions": [
                {
                    "event_name": "continue_guest"
                },
                {
                    "event_name": "login"
                },
                {
                    "event_name": "back"
                },
            ],
            "initial_state": False,
            "final_state": False,
        },
        {
            "state_type": "screen",
            "name": "LoginFlowScreen",
            "transitions": [
                {
                    "case": "login_success",
                    "state_id": "ShippingAddressScreen"
                },
                {
                    "case": "cancel",
                    "state_id": "GuestCheckoutScreen"
                },
            ],
            "expressions": [
                {
                    "event_name": "login_success"
                },
                {
                    "event_name": "cancel"
                },
            ],
            "initial_state": False,
            "final_state": False,
        },
        {
            "state_type": "screen",
            "name": "ShippingAddressScreen",
            "transitions": [
                {
                    "case": "next",
                    "state_id": "ValidateAddress"
                },
                {
                    "case": "back",
                    "state_id": "CartReviewScreen"
                },
            ],
            "expressions": [
                {
                    "event_name": "next"
                },
                {
                    "event_name": "back"
                },
            ],
            "initial_state": False,
            "final_state": False,
        },
        {
            "state_type": "integration",
            "name": "ValidateAddress",
            "transitions": [
                {
                    "variable": "address",
                    "case": None,
                    "state_id": "CheckAddressValidation",
                },  # Single transition to technical state
            ],
            "expressions": [
                {
                    "variable": "address",
                    "url": "http://localhost:8080",
                    "params": {},
                    "method": "get",
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
                    "dependent_variables": [
                        "address"
                    ],
                    "expression": "'<title>' in address",  # This will evaluate the API response
                }
            ],
            "initial_state": False,
            "final_state": False,
        },
        {
            "state_type": "screen",
            "name": "PaymentMethodScreen",
            "transitions": [
                {
                    "case": "credit_card",
                    "state_id": "CardPaymentScreen"
                },
                {
                    "case": "paypal",
                    "state_id": "PayPalFlow"
                },
                {
                    "case": "back",
                    "state_id": "ShippingAddressScreen"
                },
            ],
            "expressions": [
                {
                    "event_name": "credit_card"
                },
                {
                    "event_name": "paypal"
                },
                {
                    "event_name": "back"
                },
            ],
            "initial_state": False,
            "final_state": False,
        },
        {
            "state_type": "screen",
            "name": "CardPaymentScreen",
            "transitions": [
                {
                    "case": "pay",
                    "state_id": "ProcessPayment"
                },
                {
                    "case": "back",
                    "state_id": "PaymentMethodScreen"
                },
            ],
            "expressions": [
                {
                    "event_name": "pay"
                },
                {
                    "event_name": "back"
                },
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
                    "method": "get",
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
                    "dependent_variables": [
                        "paypal_success"
                    ],
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
                    "variable": "payment",
                },  # Single transition to technical state
            ],
            "expressions": [
                {
                    "variable": "payment",
                    "url": "http://localhost:8080",
                    "params": {},
                    "method": "get",
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
                    "dependent_variables": [
                        "payment"
                    ],
                    "expression": "'DOCTYPE' in payment",  # This will evaluate the API response
                }
            ],
            "initial_state": False,
            "final_state": False,
        },
        {
            "state_type": "screen",
            "name": "PaymentErrorScreen",
            "transitions": [
                {
                    "case": "retry",
                    "state_id": "CardPaymentScreen"
                },
                {
                    "case": "change_method",
                    "state_id": "PaymentMethodScreen"
                },
                {
                    "case": "cancel",
                    "state_id": "ExitFlow"
                },
            ],
            "expressions": [
                {
                    "event_name": "retry"
                },
                {
                    "event_name": "change_method"
                },
                {
                    "event_name": "cancel"
                },
            ],
            "initial_state": False,
            "final_state": False,
        },
        {
            "state_type": "screen",
            "name": "OrderConfirmation",
            "transitions": [
                {
                    "case": "done",
                    "state_id": "ExitFlow"
                },
            ],
            "expressions": [
                {
                    "event_name": "done"
                },
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
                        "total_amount": "49.99"
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
                        "total_amount": "25.99"
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


def test_workflow_3_banking_transaction():
    """Сложный workflow для банковской транзакции с верификацией"""
    test_json = {
        "states": [
            {
                "state_type": "technical",
                "name": "InitTransaction",
                "transitions": [
                    {
                        "variable": "has_sufficient_funds",
                        "case": "True",
                        "state_id": "SecurityCheck",
                    },
                    {
                        "variable": "has_sufficient_funds",
                        "case": "False",
                        "state_id": "InsufficientFundsScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "has_sufficient_funds",
                        "dependent_variables": ["account_balance", "transaction_amount"],
                        "expression": "account_balance >= transaction_amount",
                    }
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "InsufficientFundsScreen",
                "transitions": [
                    {
                        "case": "add_funds",
                        "state_id": "ExitFlow"
                    },
                    {
                        "case": "cancel",
                        "state_id": "ExitFlow"
                    },
                ],
                "expressions": [
                    {
                        "event_name": "add_funds"
                    },
                    {
                        "event_name": "cancel"
                    },
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "SecurityCheck",
                "transitions": [
                    {
                        "variable": "security_response",
                        "case": None,
                        "state_id": "ProcessSecurityResult",
                    },
                ],
                "expressions": [
                    {
                        "variable": "security_response",
                        "url": "http://localhost:8080/security",
                        "params": {},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ProcessSecurityResult",
                "transitions": [
                    {
                        "variable": "needs_2fa",
                        "case": "True",
                        "state_id": "TwoFactorScreen",
                    },
                    {
                        "variable": "needs_2fa",
                        "case": "False",
                        "state_id": "ExecuteTransaction",
                    },
                ],
                "expressions": [
                    {
                        "variable": "needs_2fa",
                        "dependent_variables": ["security_response"],
                        "expression": "'require_2fa' in security_response",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "TwoFactorScreen",
                "transitions": [
                    {
                        "case": "verify_code",
                        "state_id": "Verify2FA"
                    },
                    {
                        "case": "cancel",
                        "state_id": "ExitFlow"
                    },
                ],
                "expressions": [
                    {
                        "event_name": "verify_code"
                    },
                    {
                        "event_name": "cancel"
                    },
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "Verify2FA",
                "transitions": [
                    {
                        "variable": "verification_result",
                        "case": None,
                        "state_id": "Check2FAResult",
                    },
                ],
                "expressions": [
                    {
                        "variable": "verification_result",
                        "url": "http://localhost:8080/verify2fa",
                        "params": {},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "Check2FAResult",
                "transitions": [
                    {
                        "variable": "verification_success",
                        "case": "True",
                        "state_id": "ExecuteTransaction",
                    },
                    {
                        "variable": "verification_success",
                        "case": "False",
                        "state_id": "TwoFactorScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "verification_success",
                        "dependent_variables": ["verification_result"],
                        "expression": "'success' in verification_result",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "ExecuteTransaction",
                "transitions": [
                    {
                        "variable": "transaction_result",
                        "case": None,
                        "state_id": "ExitFlow",
                    },
                ],
                "expressions": [
                    {
                        "variable": "transaction_result",
                        "url": "http://localhost:8080/execute",
                        "params": {},
                        "method": "post",
                    }
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


def generate_test_scenarios_banking_transaction():
    scenarios = {}

    # Scenario 1: Successful transaction with 2FA
    scenarios["successful_with_2fa"] = {
        "description": "Successful transaction requiring 2FA verification",
        "events": [
            {
                "event_name": None,
                "context": {
                    "account_balance": 1000.0,
                    "transaction_amount": 500.0,
                    "user_id": "user123"
                }
            },
            {
                "event_name": "verify_code",
                "context": {
                    "verification_code": "123456"
                }
            }
        ],
        "expected_final_state": "ExitFlow"
    }

    # Scenario 2: Insufficient funds
    scenarios["insufficient_funds"] = {
        "description": "Transaction fails due to insufficient funds",
        "events": [
            {
                "event_name": None,
                "context": {
                    "account_balance": 100.0,
                    "transaction_amount": 500.0
                }
            },
            {
                "event_name": "cancel",
                "context": {}
            }
        ],
        "expected_final_state": "ExitFlow"
    }

    # Scenario 3: 2FA failure and retry
    scenarios["2fa_retry"] = {
        "description": "Failed 2FA verification with retry",
        "events": [
            {
                "event_name": None,
                "context": {
                    "account_balance": 1000.0,
                    "transaction_amount": 300.0
                }
            },
            {
                "event_name": "verify_code",
                "context": {
                    "verification_code": "wrong_code"
                }
            },
            {
                "event_name": "verify_code",
                "context": {
                    "verification_code": "correct_code"
                }
            }
        ],
        "expected_final_state": "ExitFlow"
    }

    return scenarios


def test_workflow_4_document_approval():
    """Workflow для процесса согласования документа"""
    test_json = {
        "states": [
            {
                "state_type": "technical",
                "name": "InitApproval",
                "transitions": [
                    {
                        "variable": "document_valid",
                        "case": "True",
                        "state_id": "GetApprovers",
                    },
                    {
                        "variable": "document_valid",
                        "case": "False",
                        "state_id": "ValidationErrorScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "document_valid",
                        "dependent_variables": ["document_size", "document_type"],
                        "expression": "document_size < 10000000 and document_type in ['pdf', 'docx']",
                    }
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ValidationErrorScreen",
                "transitions": [
                    {
                        "case": "fix_document",
                        "state_id": "ExitFlow"
                    },
                    {
                        "case": "cancel",
                        "state_id": "ExitFlow"
                    },
                ],
                "expressions": [
                    {
                        "event_name": "fix_document"
                    },
                    {
                        "event_name": "cancel"
                    },
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "GetApprovers",
                "transitions": [
                    {
                        "variable": "approvers_list",
                        "case": None,
                        "state_id": "CheckApproversCount",
                    },
                ],
                "expressions": [
                    {
                        "variable": "approvers_list",
                        "url": "http://localhost:8080/approvers",
                        "params": {},
                        "method": "get",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "CheckApproversCount",
                "transitions": [
                    {
                        "variable": "has_approvers",
                        "case": "True",
                        "state_id": "SendForApproval",
                    },
                    {
                        "variable": "has_approvers",
                        "case": "False",
                        "state_id": "NoApproversScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "has_approvers",
                        "dependent_variables": ["approvers_list"],
                        "expression": "'approvers' in approvers_list and len(approvers_list) > 0",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "NoApproversScreen",
                "transitions": [
                    {
                        "case": "assign_manually",
                        "state_id": "SendForApproval"
                    },
                    {
                        "case": "cancel",
                        "state_id": "ExitFlow"
                    },
                ],
                "expressions": [
                    {
                        "event_name": "assign_manually"
                    },
                    {
                        "event_name": "cancel"
                    },
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "SendForApproval",
                "transitions": [
                    {
                        "variable": "approval_status",
                        "case": None,
                        "state_id": "CheckApprovalStatus",
                    },
                ],
                "expressions": [
                    {
                        "variable": "approval_status",
                        "url": "http://localhost:8080/approve",
                        "params": {},
                        "method": "post",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "CheckApprovalStatus",
                "transitions": [
                    {
                        "variable": "is_approved",
                        "case": "True",
                        "state_id": "ApprovalSuccessScreen",
                    },
                    {
                        "variable": "is_approved",
                        "case": "False",
                        "state_id": "ApprovalRejectedScreen",
                    },
                ],
                "expressions": [
                    {
                        "variable": "is_approved",
                        "dependent_variables": ["approval_status"],
                        "expression": "'approved' in approval_status",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ApprovalSuccessScreen",
                "transitions": [
                    {
                        "case": "done",
                        "state_id": "ExitFlow"
                    },
                ],
                "expressions": [
                    {
                        "event_name": "done"
                    },
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ApprovalRejectedScreen",
                "transitions": [
                    {
                        "case": "revise",
                        "state_id": "ExitFlow"
                    },
                    {
                        "case": "appeal",
                        "state_id": "SendForApproval"
                    },
                ],
                "expressions": [
                    {
                        "event_name": "revise"
                    },
                    {
                        "event_name": "appeal"
                    },
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


def generate_test_scenarios_document_approval():
    scenarios = {}

    # Scenario 1: Successful approval flow
    scenarios["successful_approval"] = {
        "description": "Document successfully approved",
        "events": [
            {
                "event_name": None,
                "context": {
                    "document_size": 5000000,
                    "document_type": "pdf",
                    "document_id": "doc123"
                }
            },
            {
                "event_name": "done",
                "context": {}
            }
        ],
        "expected_final_state": "ExitFlow"
    }

    # Scenario 2: Invalid document
    scenarios["invalid_document"] = {
        "description": "Document validation fails",
        "events": [
            {
                "event_name": None,
                "context": {
                    "document_size": 15000000,
                    "document_type": "txt"
                }
            },
            {
                "event_name": "cancel",
                "context": {}
            }
        ],
        "expected_final_state": "ExitFlow"
    }

    # Scenario 3: Rejection with appeal
    scenarios["rejection_with_appeal"] = {
        "description": "Document rejected but appealed",
        "events": [
            {
                "event_name": None,
                "context": {
                    "document_size": 3000000,
                    "document_type": "docx"
                }
            },
            {
                "event_name": "appeal",
                "context": {
                    "appeal_reason": "Updated content"
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
