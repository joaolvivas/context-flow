# Repository Guidelines

## Project Structure & Module Organization
ContextFlow’s FastAPI proxy lives in `src/contextflow/`; `main.py` exposes the ASGI entrypoint and wires rate limiting, logging, and memory routing. Core memory logic is split into `modules/` (routing tiers and bridges), `models/` (Pydantic request/response schemas), and `utils/` (logging, metrics). Configurable defaults and pricing tables sit in `config.py`. Operational docs live in `docs/`, helper automation in `scripts/` (start/stop/test wrappers), integration samples in `examples/`, and pytest plus smoke scripts under `tests/`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a local environment.
- `pip install -r requirements.txt`: install runtime and testing dependencies.
- `uvicorn src.contextflow.main:app --reload`: run the proxy locally on port 8000.
- `scripts/start.sh`: launch the proxy together with the Graphiti HTTP bridge (requires `.env`).
- `pytest tests`: execute Python unit tests; use `bash tests/test_3_tier_memory.sh` for end-to-end validation.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and snake_case for modules, functions, and variables; classes stay in PascalCase as in `models/request_models.py`. Format code with `black src/` and keep imports sorted via `isort`. Run `flake8 src/` for linting and `mypy src/` to enforce the type hints already present in the models, routers, and utilities.

## Testing Guidelines
Unit tests live in `tests/test_session_memory.py`; replicate the async patterns already used there when exercising new routers or utilities. Place new suites under `tests/` using the `test_*.py` naming convention, and provide focused fixtures for Redis or API clients instead of broad mocks. Re-run the shell smoke scripts in `tests/` after modifying bridging logic, and capture expected responses with `pytest -k name -vv` when debugging.

## Commit & Pull Request Guidelines
Use Conventional Commits (e.g., `feat: add tier-4 fallback router`, `fix: guard redis reconnect`) to keep the changelog automation accurate. Each PR should describe the behavior change, link any issues, and note how you validated the update (tests, manual curl run, etc.). Update `CHANGELOG.md` and relevant docs when altering APIs or configuration, and include screenshots or logs whenever UI dashboards or metrics output change.

## Security & Configuration Tips
Copy `.env.example` to `.env`, populate provider API keys, and keep the file out of version control. `scripts/start.sh` expects reachable Redis and Graphiti endpoints; adjust `settings.memory_backend` and related URLs in `.env` when swapping providers. Never embed secrets in code—reference them through `config.py` fields so FastAPI and the bridges pick them up at startup.
