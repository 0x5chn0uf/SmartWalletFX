#!/bin/bash

# Run Flake8 for linting
flake8 backend/

# Run Bandit for security analysis
bandit -r backend/

# Run Pytest for testing
pytest backend/

# Run MyPy for type checking
mypy backend/

# Run Ruff for additional linting
ruff backend/ 