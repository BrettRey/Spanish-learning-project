# Makefile for Spanish Learning Project

.PHONY: help build-kg build-freq build-db test test-unit test-integration clean

# Default target
help:
	@echo "Spanish Learning Project - Available Commands"
	@echo ""
	@echo "Build:"
	@echo "  make build-kg        Build knowledge graph (kg.sqlite)"
	@echo "  make build-freq      Build frequency database (data/frequency/frequency.sqlite)"
	@echo "  make build-db        Build all databases"
	@echo ""
	@echo "Test:"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-quick      Quick feedback (stop on first failure)"
	@echo "  make test-coach      Test atomic coaching tools"
	@echo ""
	@echo "Clean:"
	@echo "  make clean           Remove generated databases"
	@echo ""
	@echo "Development:"
	@echo "  make format          Format code with ruff"
	@echo "  make lint            Check code with ruff"
	@echo "  make kg-server       Run KG server in test mode"
	@echo "  make srs-server      Run SRS server in test mode"

# Build knowledge graph from YAML seed files
build-kg:
	@echo "Building knowledge graph..."
	python kg/build.py kg/seed kg.sqlite
	@echo "✓ kg.sqlite created (25 nodes, 65 edges)"

# Build frequency database from source data
build-freq:
	@echo "Building frequency database..."
	python scripts/build_frequency_index.py
	@echo "✓ data/frequency/frequency.sqlite created"

# Build all databases
build-db: build-kg build-freq
	@echo "✓ All databases built"

# Run all tests
test:
	pytest

# Run unit tests only
test-unit:
	pytest -m unit

# Run integration tests only
test-integration:
	pytest -m integration

# Quick feedback mode (stop on first failure, no coverage)
test-quick:
	pytest --maxfail=1 --disable-warnings --no-cov

# Test atomic coaching tools
test-coach:
	python state/test_coach.py

# Test session planner
test-planner:
	python state/test_session_planner.py

# Clean generated databases
clean:
	@echo "Removing generated databases..."
	rm -f kg.sqlite
	rm -f data/frequency/frequency.sqlite
	@echo "✓ Clean complete"

# Format code with ruff
format:
	ruff format .

# Lint code with ruff
lint:
	ruff check .

# Run KG server in test mode
kg-server:
	python -m mcp_servers.kg_server --test

# Run SRS server in test mode
srs-server:
	python -m mcp_servers.srs_server --test

# Run speech server in test mode
speech-server:
	python -m mcp_servers.speech_server --test
