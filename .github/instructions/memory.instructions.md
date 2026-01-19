---
applyTo: '**'
---

# Meal Planner Development Guidelines

## ⚠️ MANDATORY Pre-Commit Checklist ⚠️

**CRITICAL: Before ending your turn or considering work complete, you MUST ALWAYS run the full CI check suite locally and verify all checks pass.**

**Skipping CI checks is NOT acceptable - even for documentation-only changes.**

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

**ALL** of the following must pass with **ZERO errors** before work is considered complete:
- ✓ Backend ruff linting (`uv run ruff check app/ tests/`)
- ✓ Backend mypy type checking (`uv run mypy app/ --ignore-missing-imports`)
- ✓ Backend pytest tests (`uv run pytest tests/ --cov=app`)
- ✓ Frontend linting (`npm run lint`)
- ✓ Frontend tests with coverage (`npm run test -- --coverage`)
- ✓ Frontend build (`npm run build`)
- ✓ Docker image builds (optional but recommended)

**No exceptions - all checks must pass before calling final report_progress or completing work.**

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

- **CRITICAL**: Always ensure dependencies are installed before running checks
- **REQUIRED**: Use `uv run` prefix for all Python commands in the backend
- Environment variables are loaded from `.env` file for local runs
- Docker builds require Docker/Podman to be installed
- **MANDATORY**: Run ALL CI checks before considering work complete - no exceptions
