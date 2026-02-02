# Makefile for Juniper Mist Multi Site Provisioning Service
export PYTHONPATH := .
export PYTHONWARNINGS := ignore

# Virtual environment paths
VENV := .venv
ifeq ($(OS),Windows_NT)
	PYTHON := $(VENV)\Scripts\python.exe
	PIP := $(VENV)\Scripts\pip.exe
	RUFF := $(VENV)\Scripts\ruff.exe
	SHELL := powershell.exe
	.SHELLFLAGS := -NoProfile -Command
else
	PYTHON := $(VENV)/bin/python
	PIP := $(VENV)/bin/pip
	RUFF := $(VENV)/bin/ruff
endif

# Create virtual environment
venv:
	python -m venv $(VENV)
	@echo "Virtual environment created. Run 'make install' to install dependencies."

# Install dependencies
install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Dependencies installed successfully."

# Run lint, tests, then start server
run:
	$(RUFF) check . --fix; $(PYTHON) -m pytest tests/; if ($$LASTEXITCODE -eq 0) { $(PYTHON) -m hypercorn src.main:app --reload }

# Lint with auto-fix
lint:
	$(RUFF) check . --fix

# Lint then run tests
test: lint
	$(PYTHON) -m pytest tests/ -v

# Start server only
serve:
	$(PYTHON) -m hypercorn src.main:app --reload --bind 0.0.0.0:8000

# Clean up
clean:
	rm -rf $(VENV) __pycache__ .pytest_cache src/__pycache__ tests/__pycache__

# Show help
help:
	@echo "Available commands:"
	@echo "  make venv     - Create virtual environment"
	@echo "  make install  - Create venv and install requirements"
	@echo "  make run      - Run tests then start server"
	@echo "  make test     - Run tests only"
	@echo "  make lint     - Lint and auto-fix with ruff"
	@echo "  make serve    - Start server only"
	@echo "  make clean    - Remove venv and cache files"
	@echo ""
	@echo "Cross-platform support:"
	@echo "  Windows: Uses .venv/Scripts/python.exe"
	@echo "  Linux/Mac: Uses .venv/bin/python"

.PHONY: venv install run test lint serve clean help
