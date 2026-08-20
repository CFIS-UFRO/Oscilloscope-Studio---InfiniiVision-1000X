# Repository agent instructions

## Project architecture

- The project targets Python 3.12 and uses `uv` for dependency and environment management.
- `app/main.py` supervises the FastAPI backend and PySide6 frontend as separate processes.
- `app/src/contracts/` contains shared Pydantic schemas used across process boundaries. Keep related contract models together and do not duplicate them in the frontend or backend.
- `app/src/utils/` contains cross-cutting utilities that are independent of frontend and backend presentation layers.
- The backend must not import frontend modules. The frontend must access backend behavior through HTTP clients and shared contracts, not backend service imports.
- Keep human-facing setup, usage, and project context in `README.md`; keep implementation rules and agent guidance in this file.

## Development commands

Run commands from `app/` unless a command explicitly targets the repository root.

```bash
uv run python main.py
uv run python -m src.backend
uv run python -m src.frontend
```

## Shared code conventions

- Write code, documentation, identifiers, comments, and commit messages in English.
- Use f-strings when embedding variables in strings.
- Use concise domain names for function-only modules; do not repeat the parent package name unnecessarily.
- Follow the existing section separator style: a three-line dashed separator for major titled sections and a single dashed separator between closely related definitions.
- Do not create tests unless the user explicitly asks for them. Still run focused compilation, import, or smoke checks appropriate to the changed code.
- Do not add production dependencies unless the requested change requires them.

## Frontend architecture

Organize `app/src/frontend/` by responsibility and visual scope:

- `windows/`: top-level `QMainWindow` and `QDialog` classes that compose widgets and coordinate user flows.
- `widgets/common/`: visual controls reused by unrelated features.
- `widgets/<feature>/`: visual controls owned by one feature or window area.
- `components/`: reusable non-visual behavior, including `QObject` tasks, data loading, configuration, and presentation formatting.
- `clients/`: backend HTTP requests and response validation.
- `models/`: frontend-only data models that do not duplicate shared contracts.
- `utils/`: small, stateless helpers such as theme and path resolution.
- `assets/`: icons, help pages, and other packaged static files.

### Frontend dependency boundaries

- Windows may compose widgets and coordinate components and clients.
- Widgets may depend on components, models, contracts, and utilities, but should not perform backend HTTP requests directly.
- Components must not create, import, or own widgets or windows.
- Clients must remain independent of widgets and windows and must validate backend responses with shared contracts.
- Avoid new widget-to-window imports because they invert the normal composition direction. `HelpButton` currently owns a `HelpWindow` as a focused exception; do not copy this pattern, and prefer a signal or callback if that flow is refactored.
- Keep frontend imports under `src.frontend`; never import `src.backend` implementation modules.

### PySide6 conventions

- Keep top-level window orchestration in `windows/` and reusable visual behavior in `widgets/`.
- Place non-visual `QObject` lifecycle managers in `components/`.
- Keep potentially slow, unbounded, or external network and filesystem operations off the Qt event loop. Small reads of packaged local assets and bounded local-backend calls may remain synchronous when they cannot noticeably block the interface.
- Use the existing worker-thread pattern for release checks, downloads, and other long-running operations.
- Give Qt child widgets a parent when constructing them and preserve explicit ownership for background threads and workers.
- Use Qt signals for user intent and cross-component events rather than tightly coupling unrelated widgets.
- Resolve packaged assets through `src.frontend.utils.paths`; do not construct asset paths ad hoc.
- Respect the current Qt palette and existing theme helpers when adding custom colors or icons.

### Frontend naming and verification

- A custom public frontend class and its module must match exactly in `PascalCase` and `snake_case`, for example `ReleaseUpdateWindow` in `release_update_window.py`.
- Keep one custom public frontend class per module. A private worker may live with the public component it supports.
- Use feature-specific widget packages when a widget is not broadly reusable.
- After moving frontend modules, search the entire `app/` tree for stale imports.
- For structural changes, run `uv run python -m compileall -q src/frontend` and focused import checks from `app/`.
- For UI composition changes, use an offscreen Qt smoke check when practical; avoid constructing windows that make backend requests unless the backend is available or the request is isolated.

## Backend architecture

Organize `app/src/backend/` by responsibility:

- `application.py`: FastAPI application creation, middleware, and top-level router registration.
- `server.py`: backend process startup, logging initialization, and temporary-directory lifecycle.
- `api/router.py`: versioned API router composition.
- `api/routes/`: HTTP endpoint definitions, request/response mapping, and translation of domain errors to HTTP errors.
- `services/`: backend business logic, external I/O, release handling, and data retrieval.
- `utils/`: small backend-only helpers for paths, time formatting, and temporary files.
- `assets/`: backend-owned static data and files.

### Backend dependency boundaries

- Keep route handlers thin. Move reusable logic, external requests, filesystem operations, and release processing into `services/`.
- Services may use contracts and utilities but must not depend on FastAPI route objects or frontend modules.
- Use models from `src.contracts.api` as endpoint response models and process-boundary schemas.
- Keep artifact and updater schemas in their existing `src.contracts` packages rather than defining service-local duplicates.
- Register new feature routers through `src.backend.api.router` and keep the `/api/v1` prefix centralized there.

### FastAPI and service conventions

- Declare explicit response models and return annotations for endpoints.
- Translate expected service failures into intentional `HTTPException` status codes at the route boundary; do not expose raw implementation exceptions.
- Use synchronous route functions for blocking standard-library network or filesystem operations unless the work is explicitly moved off the event loop.
- Keep backend URLs, timeouts, host settings, and other deployment values in `src.config`.
- Use `pathlib.Path` and the centralized path modules instead of hard-coded filesystem paths.
- Use `src.backend.utils.tmp` for managed temporary files and preserve cleanup behavior.
- Preserve release integrity checks and safe staging behavior when changing update code.

### Backend naming and verification

- Name route and service modules after their API domain, using concise singular or plural nouns consistently with neighboring modules.
- Keep private service data structures private with a leading underscore unless they are intentionally shared contracts.
- After backend structural changes, search the entire `app/` tree for stale imports.
- Run `uv run python -m compileall -q src/backend` and focused application import checks from `app/`.
- Do not make live external requests as part of a smoke check unless the user explicitly asks for integration verification.

## Change discipline

- Preserve unrelated user changes in a dirty worktree.
- Keep changes scoped to the requested behavior and update imports whenever modules move.
- When asked to commit, inspect staged and unstaged diffs first, group changes by logical concern, and report the resulting commit hash and message.
- Do not pull, fetch, push, or perform other networked Git operations unless explicitly requested.
