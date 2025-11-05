# Testing Guide for Spanish Learning Coach

This directory contains the comprehensive test suite for the Spanish language learning coach system. The tests are organized to mirror the codebase structure and use pytest best practices.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Fixtures](#test-fixtures)
- [Testing Approach](#testing-approach)
- [Writing Tests](#writing-tests)
- [Coverage](#coverage)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## Overview

The test suite validates:

- **Knowledge Graph (KG)**: Node and edge creation, queries, prerequisite chains
- **FSRS Algorithm**: Stability/difficulty calculations, scheduling, review cycles
- **MCP Servers**: KG server tools (kg.next, kg.prompt) and SRS server tools (srs.due, srs.update)
- **Database Schemas**: SQLite database integrity and constraints
- **Integration Flows**: Complete workflows combining multiple components

### Test Statistics

- **Total Test Files**: 4
- **Test Categories**: Unit, Integration, Slow
- **Markers**: kg, srs, mcp, fsrs
- **Coverage Target**: 70% minimum

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures for all tests
├── test_kg_build.py              # KG building and queries (27 tests)
├── test_fsrs.py                  # FSRS algorithm calculations (18 tests)
├── mcp_servers/
│   ├── test_kg_server.py         # KG MCP tools (15 tests)
│   └── test_srs_server.py        # SRS MCP tools (18 tests)
└── README.md                      # This file
```

### Test Organization Principles

1. **Mirror Source Structure**: Test files parallel the source code structure
2. **Single Responsibility**: Each test file focuses on one module
3. **Clear Naming**: Test names describe what they verify
4. **Markers for Filtering**: Use pytest markers to run subsets of tests

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run tests in a specific file
pytest tests/test_kg_build.py

# Run tests in a directory
pytest tests/mcp_servers/

# Run a specific test
pytest tests/test_fsrs.py::test_calculate_initial_stability
```

### Using Markers

Tests are marked by category and functionality:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only KG-related tests
pytest -m kg

# Run only SRS-related tests
pytest -m srs

# Run only FSRS algorithm tests
pytest -m fsrs

# Run only MCP server tests
pytest -m mcp

# Combine markers (OR logic)
pytest -m "kg or srs"

# Combine markers (AND logic)
pytest -m "unit and kg"

# Exclude slow tests
pytest -m "not slow"
```

### Development Workflow

```bash
# Quick feedback: stop on first failure
pytest --maxfail=1

# Watch mode (requires pytest-watch)
pytest-watch

# Run recently failed tests first
pytest --failed-first

# Show local variables in failures
pytest --showlocals

# Disable warnings for cleaner output
pytest --disable-warnings

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov

# Generate HTML coverage report
pytest --cov --cov-report=html

# View coverage report
open htmlcov/index.html

# Show missing lines
pytest --cov --cov-report=term-missing

# Coverage for specific module
pytest --cov=kg tests/test_kg_build.py
```

## Test Fixtures

All shared fixtures are defined in `tests/conftest.py`. They provide reusable test data and resources.

### Database Fixtures

#### `tmp_kg_db(tmp_path) -> Path`

Creates a temporary KG SQLite database with complete schema.

**Tables**: `nodes`, `edges`, `evidence`

**Usage**:
```python
def test_kg_query(tmp_kg_db):
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.execute("SELECT * FROM nodes")
    # ...
```

#### `tmp_mastery_db(tmp_path) -> Path`

Creates a temporary mastery database with FSRS schema.

**Tables**: `items`, `review_history`

**Views**: `due_items`

**Usage**:
```python
def test_srs_scheduling(tmp_mastery_db):
    conn = sqlite3.connect(tmp_mastery_db)
    cursor = conn.execute("SELECT * FROM due_items")
    # ...
```

#### `populated_kg_db(tmp_kg_db, sample_nodes, sample_edges) -> Path`

Returns a KG database pre-populated with sample nodes and edges.

**Includes**:
- 8 sample nodes (lexemes, constructions, functions)
- 7 sample edges (prerequisites, realizations, contrasts)

**Usage**:
```python
def test_frontier_query(populated_kg_db):
    conn = sqlite3.connect(populated_kg_db)
    # Query against populated data
```

#### `populated_mastery_db(tmp_mastery_db, sample_learner) -> Path`

Returns a mastery database with sample items and review history.

**Includes**:
- 4 items at different mastery stages
- Review history for items with reps > 0

### Configuration Fixtures

#### `sample_learner() -> dict[str, Any]`

Provides a sample A2 learner configuration.

**Fields**: learner_id, cefr_current, cefr_goal, topics_of_interest, session_preferences

**Usage**:
```python
def test_learner_preferences(sample_learner):
    assert sample_learner["cefr_current"] == "A2"
```

#### `advanced_learner() -> dict[str, Any]`

Provides a B2 learner configuration for testing edge cases.

#### `fsrs_default_params() -> dict[str, Any]`

Provides default FSRS algorithm parameters.

**Includes**: 17 weights, request_retention, maximum_interval, feature flags

### Data Fixtures

#### `sample_nodes() -> list[dict[str, Any]]`

Returns 8 sample KG nodes spanning A1-B1 levels.

**Node Types**: Lexeme, Construction, Morph, Function, CanDo, Topic

#### `sample_edges() -> list[dict[str, Any]]`

Returns 7 sample edges showing various relationship types.

**Edge Types**: prerequisite_of, realizes, contrasts_with, depends_on, practice_with

#### `sample_kg_yaml(tmp_path) -> Path`

Creates a YAML file with sample KG data for testing parsers.

#### `mock_mcp_context() -> dict[str, Any]`

Provides a mock MCP server context for testing tools.

## Testing Approach

### Test Categories

#### Unit Tests (Marker: `@pytest.mark.unit`)

- Test individual functions in isolation
- Use mocks/stubs for dependencies
- Fast execution (< 100ms per test)
- No external resources (files, networks)

**Example**:
```python
@pytest.mark.unit
@pytest.mark.kg
def test_insert_single_node(tmp_kg_db):
    # Test a single database operation
    conn = sqlite3.connect(tmp_kg_db)
    # ...
```

#### Integration Tests (Marker: `@pytest.mark.integration`)

- Test multiple components together
- May use real databases (temporary)
- Slower execution (< 1s per test)
- Test complete workflows

**Example**:
```python
@pytest.mark.integration
@pytest.mark.srs
def test_complete_srs_workflow(populated_mastery_db):
    # Test query -> update -> verify cycle
    # ...
```

#### Slow Tests (Marker: `@pytest.mark.slow`)

- Tests taking > 1 second
- Complex calculations or large datasets
- Run separately in CI

### Testing Philosophy

#### Red-Green-Refactor

Many tests are currently "stubs" or "placeholders" that define the expected interface:

1. **Red**: Tests exist but implementations don't (tests would fail if run)
2. **Green**: Implement the actual code to make tests pass
3. **Refactor**: Improve implementation while keeping tests green

**Stub Pattern**:
```python
def test_kg_next_returns_nodes(populated_kg_db):
    # NOTE: This is a stub. Replace with actual implementation.
    # from mcp_servers.kg_server import kg_next

    # Stub implementation for reference
    def kg_next_stub(kg_db_path, learner_id, k):
        # Simple placeholder logic
        pass

    # Test the interface
    result = kg_next_stub(populated_kg_db, "learner_001", 5)
    assert isinstance(result, list)
```

#### Test-Driven Development (TDD)

When implementing new features:

1. Write the test first (what should it do?)
2. Run the test (it should fail - red)
3. Implement minimum code to pass
4. Run test again (green)
5. Refactor for clarity

#### Parametrized Tests

Use `@pytest.mark.parametrize` to test multiple cases:

```python
@pytest.mark.parametrize("rating,expected_change", [
    (1, "increase"),  # Again -> difficulty increases
    (2, "increase"),  # Hard -> difficulty increases
    (3, "stable"),    # Good -> difficulty stable
    (4, "decrease"),  # Easy -> difficulty decreases
])
def test_update_difficulty(rating, expected_change):
    # Test runs 4 times with different inputs
    # ...
```

## Writing Tests

### Test Naming Convention

```python
# Format: test_<function>_<scenario>
def test_kg_next_returns_nodes_for_learner()
def test_kg_next_respects_k_parameter()
def test_kg_next_excludes_mastered_nodes()

# Use descriptive names that explain the test
def test_srs_update_increments_reps()  # Good
def test_update()                       # Bad (not descriptive)
```

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange: Set up test data
    learner = {"learner_id": "test_001", "cefr_current": "A2"}

    # Act: Execute the function being tested
    result = some_function(learner)

    # Assert: Verify the result
    assert result["status"] == "success"
    assert len(result["nodes"]) > 0
```

### Assertion Best Practices

```python
# Use specific assertions
assert result == expected  # Good
assert result             # Bad (not specific)

# Test multiple aspects separately
assert "node_id" in node
assert "label" in node
assert node["type"] == "Lexeme"

# Use descriptive messages for complex assertions
assert len(nodes) > 0, "Should return at least one node"
assert stability > 0, f"Stability should be positive, got {stability}"
```

### Fixture Usage

```python
# Request fixtures as function parameters
def test_with_fixtures(tmp_kg_db, sample_learner):
    # Fixtures are automatically provided
    pass

# Compose fixtures (fixtures can use other fixtures)
@pytest.fixture
def populated_kg_db(tmp_kg_db, sample_nodes):
    # Use tmp_kg_db and sample_nodes
    pass
```

### Testing Exceptions

```python
# Test that exceptions are raised
def test_invalid_rating():
    with pytest.raises(ValueError):
        validate_rating(0)  # Should raise ValueError

# Test exception message
def test_invalid_rating_message():
    with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
        validate_rating(0)
```

### Testing Async Functions

```python
# Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

## Coverage

### Current Coverage Strategy

1. **Minimum Coverage**: 70% overall
2. **Critical Path**: 90%+ for FSRS algorithm and core KG queries
3. **Stubs**: Acknowledged gaps where implementations don't exist yet

### Viewing Coverage

```bash
# Terminal report
pytest --cov --cov-report=term-missing

# HTML report (recommended)
pytest --cov --cov-report=html
open htmlcov/index.html

# Coverage for specific module
pytest --cov=mcp_servers tests/mcp_servers/
```

### Coverage Configuration

Coverage settings are in `pyproject.toml`:

```toml
[tool.coverage.run]
branch = true           # Include branch coverage
source = ["kg", "mcp_servers"]
omit = ["*/tests/*"]    # Exclude test files from coverage

[tool.coverage.report]
precision = 2
show_missing = true     # Show lines not covered
```

### Improving Coverage

1. Run coverage report to identify gaps:
   ```bash
   pytest --cov --cov-report=html
   ```

2. Open `htmlcov/index.html` and click on modules

3. Red lines = not covered, green = covered

4. Write tests for uncovered lines/branches

## Continuous Integration

### CI Configuration (Example GitHub Actions)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

Consider adding `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: ['-x', '--tb=short']
```

## Troubleshooting

### Common Issues

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'kg'`

**Solution**: Install package in development mode:
```bash
pip install -e .
```

#### Fixture Not Found

**Problem**: `fixture 'sample_learner' not found`

**Solution**: Check that `conftest.py` is in the correct location and properly formatted.

#### Database Lock Errors

**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**: Ensure connections are properly closed:
```python
conn = sqlite3.connect(db_path)
try:
    # ... operations
finally:
    conn.close()
```

#### Slow Test Runs

**Problem**: Tests take too long

**Solutions**:
- Use markers to run subsets: `pytest -m unit`
- Run in parallel: `pytest -n auto`
- Skip slow tests during development: `pytest -m "not slow"`

#### Coverage Too Low

**Problem**: Coverage below 70% threshold

**Solution**: Run with verbose coverage to see what's missing:
```bash
pytest --cov --cov-report=term-missing
```

### Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace

# Print output (normally captured)
pytest -s

# Show local variables in tracebacks
pytest --showlocals

# Very verbose output
pytest -vv
```

### Getting Help

- Check test docstrings for usage examples
- Review fixture definitions in `conftest.py`
- Look at similar tests for patterns
- Run with `-v` for more detailed output

## Next Steps

### For Implementation

1. **Replace Stubs**: As you implement modules (kg/build.py, mcp_servers/), replace stub functions in tests with actual imports
2. **Add Tests**: When adding new features, write tests first (TDD)
3. **Maintain Coverage**: Keep coverage above 70%

### For Testing

1. **Integration Tests**: Add end-to-end workflow tests
2. **Performance Tests**: Add benchmarks for FSRS calculations
3. **Property-Based Tests**: Consider using Hypothesis for FSRS edge cases
4. **Mutation Testing**: Use mutmut to verify test quality

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
- [FSRS Algorithm Wiki](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

**Last Updated**: 2025-11-04

**Maintained By**: Spanish Learning Coach Development Team
