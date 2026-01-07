---
applyTo: '**'
---

# Meal Planner Development Guidelines

## Pre-Commit Checklist

**IMPORTANT: Before ending your turn or considering work complete, ALWAYS run the full CI check suite locally.**

### Running All Checks

Execute this command from the project root to run all CI checks locally:

```bash
./scripts/run-checks.sh
```

This script runs:
- **Backend**: ruff linting, mypy type checking, pytest with coverage
- **Frontend**: eslint/prettier, vitest with coverage, build
- **Docker**: Build both backend and frontend images

### What Must Pass

All of the following must pass before work is considered complete:
- ✓ Backend ruff linting (`uv run ruff check app/ tests/`)
- ✓ Backend mypy type checking (`uv run mypy app/ --ignore-missing-imports`)
- ✓ Backend pytest tests (`uv run pytest tests/ --cov=app`)
- ✓ Frontend linting (`npm run lint`)
- ✓ Frontend tests with coverage (`npm run test -- --coverage`)
- ✓ Frontend build (`npm run build`)
- ✓ Docker image builds (optional but recommended)

### Common Issues

**Backend:**
- Ruff errors: Usually whitespace/import ordering. Run `uv run ruff check app/ tests/ --fix`
- Mypy errors: Type hints - check the error message for what's missing
- Pytest failures: Run `uv run pytest tests/ -v` to see detailed output

**Frontend:**
- Lint errors: Run `npm run lint -- --fix` to auto-fix
- Test failures: Run `npm run test` to see detailed output
- Build issues: Check `npm run build` output for errors

### Important Notes

- Always ensure dependencies are installed before running checks
- Use `uv run` for Python commands in the backend
- Environment variables are loaded from `.env` file for local runs
- Docker builds require Docker/Podman to be installed
