# Copilot Instructions for Meal Planner

## ⚠️ CRITICAL PRE-COMMIT REQUIREMENTS ⚠️

**MANDATORY: Before considering ANY work complete, ending your turn, or calling report_progress for the final time, you MUST:**

1. **Run ALL quality checks locally** - Every single check must pass with zero errors
2. **Fix ALL linting, type checking, and test failures** - No exceptions
3. **Verify no regressions are introduced** - Existing tests must continue to pass
4. **Never skip CI checks** - Even for "minor" changes like documentation

**Failure to run and pass all CI checks before completing work is unacceptable and will result in CI failures.**

## Running Quality Checks

### Complete CI Check Suite

Execute from project root to run all CI checks locally:

```bash
./scripts/run-checks.sh
```

This runs all backend and frontend checks in one command.

### Individual Backend Checks

Navigate to `/backend` and run (ALWAYS use `uv run` prefix):

```bash
# Linting with ruff (auto-fix available)
uv run ruff check app/ tests/
uv run ruff check app/ tests/ --fix  # Auto-fix issues

# Type checking with mypy
uv run mypy app/ --ignore-missing-imports

# Tests with coverage
uv run pytest tests/ --cov=app
```

**IMPORTANT:** All backend checks must pass with zero errors before work is considered complete.

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

**IMPORTANT:** All frontend checks must pass with zero errors before work is considered complete.

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
- **ALWAYS run and pass all CI checks locally before considering work complete**
- Document any new features or significant changes in code comments

## Final Checklist Before Completing Work

Before your final `report_progress` or considering work complete, verify:

- [ ] `uv run ruff check app/ tests/` passes (backend)
- [ ] `uv run mypy app/ --ignore-missing-imports` passes (backend)
- [ ] `uv run pytest tests/ --cov=app` passes (backend)
- [ ] `npm run lint` passes (frontend)
- [ ] `npm run test -- --coverage` passes (frontend)
- [ ] `npm run build` passes (frontend)
- [ ] All changes have been committed via `report_progress`
- [ ] No temporary or debug files are included in commits
