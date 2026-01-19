# Copilot Instructions for Meal Planner

## Critical Pre-Commit Requirements

**IMPORTANT: Before considering work complete or ending your turn, you MUST:**

1. **Run all quality checks locally** - All checks must pass
2. **Fix any linting, type checking, or test failures**
3. **Ensure no regressions are introduced**

## Running Quality Checks

### Complete CI Check Suite

Execute from project root to run all CI checks locally:

```bash
./scripts/run-checks.sh
```

This runs all backend and frontend checks in one command.

### Individual Backend Checks

Navigate to `/backend` and run:

```bash
# Linting with ruff (auto-fix available)
ruff check app/ tests/
ruff check app/ tests/ --fix  # Auto-fix issues

# Type checking with mypy
mypy app/ --ignore-missing-imports

# Tests with coverage
pytest tests/ --cov=app
```

### Individual Frontend Checks

Navigate to `/frontend` and run:

```bash
# Linting
npm run lint
npm run lint -- --fix  # Auto-fix issues

# Tests with coverage
npm run test -- --coverage

# Build verification
npm run build
```

## Python Development Standards

### Package Management - ALWAYS Use UV

**CRITICAL:** Always use `uv` for Python commands and dependency management:

```bash
# Add dependencies
uv add <package>

# Run Python modules
uv run python -m <module>

# Run scripts
uv run <script>.py

# Run pytest
uv run pytest

# Run ruff
uv run ruff check app/
```

### Development Server Information

**IMPORTANT:** Assume services are already running:
- **Frontend**: http://localhost:3080 (with hot reload)
- **Backend**: http://localhost:8180 (with auto-reload)

Only start services if you verify they're not already running.

## Additional Instructions

See related instruction files:
- **Memory/Guidelines**: `.github/instructions/memory.instructions.md` - Development guidelines and pre-commit checklist

## Quality Gates

All of the following MUST pass before work is complete:

### Backend
- ✅ ruff linting (no errors)
- ✅ mypy type checking (no errors)
- ✅ pytest tests (all passing with adequate coverage)

### Frontend
- ✅ ESLint/Prettier linting (no errors)
- ✅ Vitest tests (all passing with adequate coverage)
- ✅ Production build succeeds

### Docker (Optional but Recommended)
- ✅ Backend image builds successfully
- ✅ Frontend image builds successfully

## Common Issues and Solutions

### Backend Issues

**Ruff Linting Errors:**
- Usually whitespace, import ordering, or unused imports
- Run `ruff check app/ tests/ --fix` to auto-fix most issues
- Use `--unsafe-fixes` flag for more aggressive fixes if needed

**Mypy Type Errors:**
- Add missing type hints
- Use `# type: ignore` only as last resort with explanation
- Check error messages for specific guidance

**Pytest Failures:**
- Run `pytest tests/ -v` for detailed output
- Check test output for specific failure reasons
- Ensure test data is set up correctly

### Frontend Issues

**Lint Errors:**
- Run `npm run lint -- --fix` to auto-fix
- Check for unused imports, variables
- Ensure consistent formatting

**Test Failures:**
- Run `npm run test` to see detailed output
- Check for missing mocks or test data
- Verify component behavior matches expectations

**Build Issues:**
- Check `npm run build` output for specific errors
- Ensure all imports resolve correctly
- Verify environment variables are available

## Important Notes

- Environment variables are loaded from `.env` file for local development
- Use proper git commit messages following conventional commits format
- Never commit sensitive data (API keys, passwords, etc.)
- Always test changes locally before considering work complete
- Document any new features or significant changes in code comments
- Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.
