# Copilot Instructions for `lct_efs`

## Project Shape
- **Workflow engine** lives under `workflow_builder/`; JSON workflows in `cart_workflow.json` or Mongo are parsed to `StateModel` via `state_parser` and executed by `automaton.Automaton`.
- **API layer** (`api/app.py`, `api/routes.py`) exposes FastAPI endpoints (notably `/client/workflow`, `/workflow/save`) that orchestrate the automaton and persistence adapters.
- **Persistence** abstractions reside in `storage/mongo/client.py` (collections: `states`, `screens`, `workflow_context`) and `storage/redis/service.py` (session + state cache via Redis).
- Configuration flows through `config.Settings`; it expects `.env` values for DB/Redis/Mongo—defaults target localhost services started from `deployments/docker-compose.yaml`.

## Documentation
- Current documentation resides in `docs/` directory (focus on `FIX_CUTE_IMAGES_TRANSITION.md` for integration state binding examples).
- Legacy/outdated markdown documentation was removed during Oct 2025 cleanup—refer to inline code comments and existing docs only.

## Key Patterns
- Every workflow run tracks state in Redis using `SessionContext`; when adding logic, persist complex objects with `json.dumps` before writing to Redis (see `SessionContext.update_session`).
- Mongo operations rely on helper methods (`insert_workflow_with_format_validation`, `upsert_screen`, `get_workflow_with_context`). Reuse them instead of raw PyMongo to preserve collection conventions.
- Integration states should prefer `body` over `params` for POST/PUT/PATCH (validated in `test_new_format.py`).
- Screens are stored separately in the `screens` collection keyed by `(workflow_id, state_id)`; keep this schema when creating new screen-saving routines.

## Working Locally
- Create/activate the virtualenv in `.venv`; install requirements with `./.venv/bin/python -m pip install -r deployments/requirements.txt`.
- Start Redis and Mongo for integration workflows via `docker-compose -f deployments/docker-compose.yaml up -d` or provide equivalent services.
- Run the API with `./.venv/bin/python -m uvicorn api.app:app --reload --port 8080`.
- Use `./.venv/bin/python -m pytest` for the full suite. Integration tests expect live Redis/Mongo; unit-style tests in `test_new_format.py` rely on `mongomock` and patching defined in the file.

## Testing Conventions
- Several historical tests return data instead of asserting; preserve behaviour unless you plan to refactor the tests (warnings are expected).
- For new tests touching Mongo, prefer the `mongomock` fixture pattern (`mongo_mock`, `workflow_id`) from `test_new_format.py` to avoid coupling to external services.
- When introducing Redis-dependent logic, consider adding helpers similar to `mongo_mock` or start Redis via Docker for the test run.

## Extending the Engine
- New state types require updates to `workflow_builder/state_parser/contract.py`, `STATE_CLASSES`, and corresponding expression wiring in `workflow_builder/expressions.py`.
- Automaton transitions are described in workflow JSON; ensure new transitions include appropriate handlers or default cases to avoid `No matching transition found` errors.
- Service states (`SERVICE_INIT_STATE`, `SERVICE_ERROR_STATE`) are injected automatically—respect these reserved names when manipulating workflow graphs.

## Cross-Cutting Notes
- Logging is initialised via `utils.setup_logging`; call it in new entry points to keep log formatting consistent.
- `config.Settings.mongo_url` and `.redis_url` URL-encode credentials; supply plain values in `.env` (quotes optional) to avoid double-encoding.
- If you require external HTTP integrations, study `adapters/commonAdapter.py` for the request pattern and interpolation behaviour.

Let me know if any area of the project is unclear or if you need deeper dives into specific subsystems.
