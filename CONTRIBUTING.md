# Contributing to 1829 Ventures CRM

## Code Standards

### Backend (Python)

This project uses **Ruff** for linting and formatting Python code. Ruff enforces consistent style, catches common mistakes, and replaces older tools like `flake8`, `isort`, and `black` in a single fast tool.

Run it before committing:

```bash
make lint
```

Ruff is configured in `backend/pyproject.toml`. Code that does not pass linting will be blocked in CI.

Type checking is handled by **mypy**, also configured in `backend/pyproject.toml`.

### Frontend (TypeScript/React)

This project uses **ESLint** for linting and **Prettier** for formatting TypeScript and React code.

Run before committing:

```bash
cd frontend && npm run lint
cd frontend && npm run format
```

ESLint is configured in `frontend/eslint.config.js`. Prettier is configured in `frontend/prettier.config.js`.

### Editor

An `.editorconfig` file at the repo root keeps indentation, line endings, and encoding consistent across editors. Most editors pick this up automatically or via a free plugin.

## Style References

- Python: [PEP 8](https://peps.python.org/pep-0008/) and [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- TypeScript: [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)

## Architecture Boundaries

Keep these boundaries intact when contributing:

- **Routes** handle HTTP only — no business logic
- **Services** enforce business rules, permissions, workflow transitions, approvals, and auditing
- **Repositories** isolate SQLAlchemy queries — no business logic
- **Integrations** wrap external systems only
- **Workers** run slow or async work outside the request/response cycle
- **Ritchie** interacts only through the typed API/MCP surface — never directly against the database
- **Human-curated CRM fields** remain the source of truth and should not be silently overwritten
