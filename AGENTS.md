# AGENTS.md

This document provides guidance for AI agents working on this project.

## Project Overview

**fressnapftracker** is an asynchronous Python client library for the Fressnapf Tracker GPS API. It provides a clean, typed interface for communicating with pet GPS trackers sold by Fressnapf.

## Project Structure

```
fressnapftracker/
├── fressnapftracker/           # Main package
│   ├── __init__.py             # Public exports
│   ├── fressnapftracker.py     # Main API client class
│   ├── exceptions.py           # Custom exceptions
│   └── models.py               # Pydantic data models
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── fixtures/               # JSON test fixtures
│   │   └── *.json
│   └── test_fressnapftracker.py
├── .github/
│   ├── workflows/              # CI/CD workflows
│   │   ├── ci.yml              # Continuous integration
│   │   ├── release.yml         # PyPI release
│   │   └── release_drafter.yml
│   └── release-drafter.yml     # Release drafter config
├── pyproject.toml              # Project configuration
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .gitignore
├── .yamllint
├── LICENSE
└── README.md
```

## Technologies & Libraries

### Runtime Dependencies

- **Python 3.13+**: Minimum supported Python version
- **httpx**: Async HTTP client for API requests
- **pydantic**: Data validation and serialization using Python type hints

### Development Dependencies

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **respx**: HTTP mocking for httpx
- **ruff**: Linting and code formatting
- **mypy**: Static type checking
- **pre-commit**: Git hooks for code quality
- **codespell**: Spell checking
- **yamllint**: YAML file linting

## Development Commands

All Python commands should be run via `uv`:

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run type checking
uv run mypy fressnapftracker

# Run linting
uv run ruff check .

# Run formatting check
uv run ruff format --check .

# Format code
uv run ruff format .

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Coding Guidelines

### Type Hints

- **Always use type hints** for all function parameters and return types
- Use modern typing syntax (e.g., `list[str]` instead of `List[str]`, `str | None` instead of `Optional[str]`)
- All Pydantic models must have proper type annotations

### Testing Requirements

- **All tests must always pass** - never submit changes with failing tests
- **Tests must never be deleted** - only add or modify tests
- **Include tests for all changed/added code** - maintain or improve coverage
- Use `respx` for mocking HTTP requests
- Place test fixtures in `tests/fixtures/` as JSON files
- Use `pytest.mark.asyncio` for async tests (auto mode is enabled)

### Code Quality

Before submitting any changes, **always run**:

```bash
uv run pre-commit run --all-files
```

This runs:
- Trailing whitespace removal
- End of file fixing
- YAML validation
- JSON formatting
- Ruff linting and formatting
- Codespell spell checking
- yamllint

All checks must pass before changes are considered complete.

### Error Handling

- Use custom exceptions from `exceptions.py`
- All exceptions inherit from `FressnapfTrackerError`
- Handle specific API errors with appropriate exception types

### Code Style

- Line length: 120 characters
- Follow ruff's default style (based on Black)
- Use docstrings for all public functions, methods, and classes
- Keep methods focused and DRY - extract common patterns into helper methods

## API Structure

The library has two types of API endpoints:

1. **Device API** (`itsmybike.cloud`): For tracker operations
   - Get tracker data
   - Set LED brightness
   - Set deep sleep mode

2. **Auth API** (`user.iot-pet-tracking.cloud`): For authentication
   - Request SMS code
   - Verify phone number
   - Get devices list

## Key Classes

- `FressnapfTrackerApi`: Main client class with async context manager support
- `Tracker`: Pydantic model for tracker data
- `Device`: Pydantic model for device information
- `Position`: Pydantic model for GPS coordinates
