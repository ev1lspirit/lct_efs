import pytest
from unittest.mock import patch

import fakeredis
from bson import ObjectId

from config import settings
from storage.mongo.client import MongoDBClient
from storage.redis.service import AsyncRedisCache
from context import SessionContext
from utils import GeneralPurposeSingletonMeta
from workflow_builder.automaton.automaton import Automaton
from workflow_builder.state_parser.workflow_cache import workflow_cache


WELCOME_SCREEN = {
    "id": "welcome-screen",
    "type": "Screen",
    "name": "Welcome",
    "sections": {},
}

CHECKOUT_SCREEN = {
    "id": "checkout-screen",
    "type": "Screen",
    "name": "Checkout",
    "sections": {},
}

EMPTY_SCREEN = {"id": "empty-screen", "type": "Screen", "name": "Empty", "sections": {}}

SIMPLE_WORKFLOW_STATES = [
    {
        "state_type": "screen",
        "name": "WelcomeScreen",
        "transitions": [{"case": "proceed", "state_id": "EvaluateCart"}],
        "expressions": [{"event_name": "proceed"}],
        "initial_state": True,
        "final_state": False,
        "screen": WELCOME_SCREEN,
    },
    {
        "state_type": "technical",
        "name": "EvaluateCart",
        "transitions": [
            {"variable": "cart_status", "case": "ready", "state_id": "CheckoutScreen"},
            {"variable": "cart_status", "case": "empty", "state_id": "EmptyCartScreen"},
        ],
        "expressions": [
            {
                "variable": "cart_status",
                "dependent_variables": ["cart_items"],
                "expression": "'ready' if len(cart_items) > 0 else 'empty'",
            }
        ],
        "initial_state": False,
        "final_state": False,
    },
    {
        "state_type": "screen",
        "name": "CheckoutScreen",
        "transitions": [],
        "expressions": [],
        "initial_state": False,
        "final_state": True,
        "screen": CHECKOUT_SCREEN,
    },
    {
        "state_type": "screen",
        "name": "EmptyCartScreen",
        "transitions": [],
        "expressions": [],
        "initial_state": False,
        "final_state": True,
        "screen": EMPTY_SCREEN,
    },
]


@pytest.fixture
def mongo_memory():
    from mongomock import MongoClient as MockMongoClient

    mock_client = MockMongoClient()

    def _client_factory(*args, **kwargs):
        return mock_client

    with patch("storage.mongo.client.MongoClient", _client_factory):
        # Rebind workflow cache to the mocked client so Automaton uses the same storage
        workflow_cache._mongo_client = MongoDBClient(
            database=settings.MONGO_DB,
            collection=settings.STATES_MONGO_COLLECTION,
        )
        workflow_cache._cache.clear()
        yield
        workflow_cache._cache.clear()


@pytest.fixture
def redis_memory(monkeypatch):
    fake_server = fakeredis.FakeServer()

    def fake_init(self):
        self.r = fakeredis.FakeRedis(server=fake_server)

    # Reset singleton so patched __init__ is applied
    GeneralPurposeSingletonMeta._GeneralPurposeSingletonMeta__instances.pop(
        AsyncRedisCache, None
    )
    monkeypatch.setattr(AsyncRedisCache, "__init__", fake_init)
    # Ensure SessionContext uses the patched Redis client
    SessionContext._redis_cache = AsyncRedisCache()
    yield
    GeneralPurposeSingletonMeta._GeneralPurposeSingletonMeta__instances.pop(
        AsyncRedisCache, None
    )


def _persist_workflow(workflow_states):
    states_client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.STATES_MONGO_COLLECTION,
    )
    screens_client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.SCREENS_MONGO_COLLECTION,
    )
    context_client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.WORKFLOW_MONGO_COLLECTION,
    )

    workflow_payload = {"states": workflow_states}
    workflow_id = states_client.insert_description(workflow_payload)
    assert workflow_id is not None

    for state in workflow_states:
        if state["state_type"] == "screen" and state.get("screen"):
            screens_client.upsert_screen(
                workflow_id=workflow_id,
                state_id=state["name"],
                screen_json=state["screen"],
            )

    # Service init state relies on predefined context document existing
    context_client.insert_description({}, overriden_id=workflow_id)
    workflow_cache.invalidate(workflow_id)
    return workflow_id


def test_automaton_processes_screen_technical_sequence(mongo_memory, redis_memory):
    workflow_id = _persist_workflow(SIMPLE_WORKFLOW_STATES)

    redis_cache = AsyncRedisCache()
    session_id = "session-automaton"

    base_context = {
        "__workflow_id": workflow_id,
        "cart_items": ["apple", "banana"],
    }
    redis_cache.update_session(session_id, base_context)
    redis_cache.save_state(
        session_id, {"name": settings.SERVICE_INIT_STATE, "type": "service"}
    )

    # First call: expect initial screen payload
    automaton = Automaton(session_id=session_id, workflow_id=workflow_id)
    first_screen = automaton.run(event_name=None)

    assert first_screen is not None
    assert first_screen["id"] == WELCOME_SCREEN["id"]

    state_snapshot = redis_cache.get_state(session_id)
    assert state_snapshot["name"] == "WelcomeScreen"

    # Second call with user event: through technical state to final screen
    automaton = Automaton(session_id=session_id, workflow_id=workflow_id)
    result = automaton.run(event_name="proceed")

    assert result is None  # final state reached, no screen returned
    assert automaton.current_state.name == "CheckoutScreen"
    assert automaton.current_state._final is True

    session_context = redis_cache.get_session(session_id)
    assert session_context["cart_status"] == "ready"
    assert session_context["cart_items"] == ["apple", "banana"]
