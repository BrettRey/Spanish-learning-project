# Knowledge Graph MCP Server

The Knowledge Graph (KG) MCP Server exposes tools for querying the language learning knowledge graph, retrieving exercise prompts, and tracking learner evidence. It is designed to integrate with the broader Spanish language learning coach system.

## Overview

This server provides three core MCP tools:

1. **kg.next**: Query frontier nodes (prerequisites satisfied, not yet mastered)
2. **kg.prompt**: Retrieve exercise scaffolds for specific nodes
3. **kg.add_evidence**: Update evidence counters based on learner performance

## Architecture

The server is designed to work with two SQLite databases:

- **kg.sqlite** (`../kg/kg.sqlite`): Knowledge graph containing nodes (linguistic items) and edges (relationships)
- **mastery.sqlite** (`../state/mastery.sqlite`): Per-learner mastery data with FSRS parameters

For development purposes, the server can run in **mock mode**, returning realistic test data without requiring actual databases.

## Installation

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)

### Setup

```bash
# From project root
cd /Users/brettreynolds/Spanish-learning-project

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (when requirements.txt is available)
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

The server can be run in multiple modes:

#### 1. Test Mode (Default)

Demonstrates all three tools with mock data:

```bash
python -m mcp_servers.kg_server --test
```

**Example Output:**

```
======================================================================
Knowledge Graph MCP Server - Test Mode
======================================================================

1. Testing kg.next (frontier nodes)
----------------------------------------------------------------------
{
  "learner_id": "test_learner",
  "count": 3,
  "nodes": [
    {
      "node_id": "constr.es.subjunctive_present",
      "type": "Construction",
      "label": "Present subjunctive",
      "cefr_level": "B1",
      "prerequisites_satisfied": true,
      "mastery_level": 0.0,
      "can_do": ["cando.es.express_doubt_B1", "cando.es.express_desire_A2"],
      "priority_score": 0.95
    },
    ...
  ]
}
```

#### 2. Interactive Mode

Manual testing with a command-line interface:

```bash
python -m mcp_servers.kg_server --interactive
```

**Available Commands:**

```
kg> next test_learner 5
kg> prompt constr.es.subjunctive_present production
kg> evidence constr.es.subjunctive_present true
kg> tools
kg> quit
```

#### 3. Server Mode (Placeholder)

Intended for MCP protocol integration (not yet fully implemented):

```bash
python -m mcp_servers.kg_server --mode server --host localhost --port 8000
```

#### 4. Real Database Mode

When the knowledge graph is built, disable mock mode:

```bash
python -m mcp_servers.kg_server --test --no-mock --kg-db ../kg/kg.sqlite
```

### Help

View all available options:

```bash
python -m mcp_servers.kg_server --help
```

## MCP Tools

### 1. kg.next

**Description:** Returns frontier nodes for a learner—nodes where prerequisites are satisfied but the node itself is not yet mastered.

**Parameters:**
- `learner_id` (string, required): Unique identifier for the learner
- `k` (integer, optional): Number of nodes to return (default: 5, max: 50)

**Returns:** JSON string with learner ID, count, and list of nodes

**Example Request:**
```python
server.kg_next(learner_id="brett", k=3)
```

**Example Response:**
```json
{
  "learner_id": "brett",
  "count": 3,
  "nodes": [
    {
      "node_id": "constr.es.subjunctive_present",
      "type": "Construction",
      "label": "Present subjunctive",
      "cefr_level": "B1",
      "prerequisites_satisfied": true,
      "mastery_level": 0.0,
      "can_do": ["cando.es.express_doubt_B1", "cando.es.express_desire_A2"],
      "priority_score": 0.95
    },
    {
      "node_id": "lexeme.es.ojalá",
      "type": "Lexeme",
      "label": "ojalá (I hope/wish that)",
      "cefr_level": "A2",
      "prerequisites_satisfied": true,
      "mastery_level": 0.2,
      "can_do": ["cando.es.express_desire_A2"],
      "priority_score": 0.88
    },
    {
      "node_id": "constr.es.por_vs_para",
      "type": "Construction",
      "label": "por vs. para distinction",
      "cefr_level": "B1",
      "prerequisites_satisfied": true,
      "mastery_level": 0.3,
      "can_do": ["cando.es.express_purpose_B1", "cando.es.express_reason_B1"],
      "priority_score": 0.82
    }
  ]
}
```

### 2. kg.prompt

**Description:** Returns an exercise scaffold for a specific knowledge graph node, including instructions, example prompts, target forms, and rubric criteria.

**Parameters:**
- `node_id` (string, required): Unique identifier for the KG node
- `kind` (string, optional): Exercise type—"production", "recognition", or "correction" (default: "production")

**Returns:** JSON string with exercise scaffold

**Example Request:**
```python
server.kg_prompt(node_id="constr.es.subjunctive_present", kind="production")
```

**Example Response:**
```json
{
  "node_id": "constr.es.subjunctive_present",
  "exercise_type": "production",
  "cefr_level": "B1",
  "instructions": "Express doubt or desire using the present subjunctive.",
  "scaffolds": [
    "No creo que... (I don't think that...)",
    "Espero que... (I hope that...)",
    "Dudo que... (I doubt that...)"
  ],
  "prompts": [
    "Express doubt about the weather tomorrow.",
    "Say what you hope your friend will do this weekend.",
    "Express uncertainty about a restaurant being open."
  ],
  "target_forms": ["present subjunctive conjugation"],
  "rubric_focus": ["form_accuracy", "pragmatic_appropriateness"]
}
```

### 3. kg.add_evidence

**Description:** Updates the evidence counter for a knowledge graph node based on learner performance. Tracks both successful and unsuccessful attempts to inform mastery calculations.

**Parameters:**
- `node_id` (string, required): Unique identifier for the KG node
- `success` (boolean, required): Whether the learner's attempt was successful

**Returns:** JSON string with updated evidence counts

**Example Request:**
```python
server.kg_add_evidence(node_id="constr.es.subjunctive_present", success=True)
```

**Example Response:**
```json
{
  "node_id": "constr.es.subjunctive_present",
  "success": true,
  "success_count": 5,
  "failure_count": 0,
  "total_attempts": 6,
  "mastery_estimate": 0.83
}
```

## Integration Points

### Current State

The server is currently implemented with **mock data** to enable development and testing before the full knowledge graph is built. All three tools (`kg.next`, `kg.prompt`, `kg.add_evidence`) return realistic Spanish language learning data.

### Future Integration

When the knowledge graph database is ready, the following integration work is needed:

#### 1. Knowledge Graph Database (`kg/kg.sqlite`)

**Expected Schema:**

```sql
-- Nodes table
CREATE TABLE nodes (
    node_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- Lexeme, Construction, Morph, Function, etc.
    label TEXT NOT NULL,
    cefr_level TEXT,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    metadata JSON  -- YAML/JSON node data
);

-- Edges table
CREATE TABLE edges (
    edge_id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,  -- prerequisite_of, realizes, etc.
    weight REAL DEFAULT 1.0,
    FOREIGN KEY (source_node_id) REFERENCES nodes(node_id),
    FOREIGN KEY (target_node_id) REFERENCES nodes(node_id)
);

-- Can-Do statements
CREATE TABLE can_do (
    can_do_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
);
```

**Required Queries:**

- **kg.next**: Query nodes where all prerequisite edges are satisfied (source nodes are mastered) and the target node is not yet mastered by the learner
- **kg.prompt**: Retrieve node metadata including prompts, scaffolds, and diagnostics
- **kg.add_evidence**: Update success/failure counters in the nodes table

#### 2. Mastery Database (`state/mastery.sqlite`)

**Expected Schema:**

```sql
CREATE TABLE mastery (
    item_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- production, recognition, etc.
    last_review TEXT,  -- ISO 8601 timestamp
    stability REAL NOT NULL,
    difficulty REAL NOT NULL,
    reps INTEGER DEFAULT 0,
    lapses INTEGER DEFAULT 0
);
```

**Integration with FSRS:**

The `kg.next` tool should cross-reference the mastery database to:
- Filter out already-mastered nodes
- Calculate priority scores based on stability and difficulty
- Integrate spaced repetition scheduling (via `srs.due()` from the SRS server)

#### 3. Implementation Checklist

To switch from mock to real data:

1. **Build the knowledge graph:**
   ```bash
   python kg/build.py seed/ kg.sqlite
   ```

2. **Update server initialization:**
   ```python
   server = KGServer(use_mock_data=False)
   ```

3. **Implement database query methods:**
   - `_query_frontier_nodes()`: Replace stub with real SQL
   - `_query_node_prompt()`: Query node metadata from `nodes` table
   - `_update_node_evidence()`: Update success/failure counters

4. **Add mastery database integration:**
   - Query `state/mastery.sqlite` to filter mastered nodes
   - Calculate mastery estimates using FSRS parameters

5. **Test with real data:**
   ```bash
   python -m mcp_servers.kg_server --test --no-mock
   ```

## Development

### Project Structure

```
mcp_servers/kg_server/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point
├── server.py            # Core KGServer implementation
└── README.md            # This file
```

### Adding New Features

1. **Add new tool methods** to `KGServer` class in `server.py`
2. **Update tool definitions** in `get_tool_definitions()`
3. **Add CLI support** in `__main__.py` if needed
4. **Document** in this README

### Testing

#### Manual Testing

Use test mode to verify all tools:

```bash
python -m mcp_servers.kg_server --test
```

#### Interactive Testing

Explore tools manually:

```bash
python -m mcp_servers.kg_server --interactive
```

#### Unit Testing (Future)

When pytest is set up:

```bash
pytest tests/test_kg_server.py
```

### Logging

The server uses Python's built-in logging module. Enable verbose logging:

```bash
python -m mcp_servers.kg_server --test --verbose
```

Logs include:
- Tool invocations with parameters
- Query execution details
- Error messages and stack traces

## Error Handling

The server defines three exception types:

- **KGServerError**: Base exception for all server errors
- **DatabaseError**: Database connection or query failures
- **NodeNotFoundError**: Requested node doesn't exist

All exceptions are caught and logged, with user-friendly error messages returned.

## Design Decisions

### 1. Mock Data First

The server is designed to work with **mock data** initially, allowing:
- Frontend development without waiting for the full KG database
- API contract validation before schema finalization
- Realistic test data for demonstrations

### 2. Separation of Concerns

- **server.py**: Core logic and MCP tool implementations
- **__main__.py**: CLI and entry point handling
- **__init__.py**: Package-level exports

This makes the code testable and allows the server to be imported as a library.

### 3. Type Hints and Error Handling

All public methods use type hints and comprehensive error handling to ensure:
- Clear API contracts
- Helpful error messages
- Production readiness

### 4. Flexible Database Paths

Database paths can be:
- Automatically resolved relative to project root
- Explicitly set via CLI arguments
- Overridden programmatically for testing

### 5. Future MCP Protocol Integration

The `--mode server` option is a placeholder for full MCP protocol support. When implemented, it will:
- Start an HTTP/JSON-RPC server
- Register tools with the MCP protocol
- Handle tool invocations from MCP clients

## Related Documentation

- **Project Overview**: `/Users/brettreynolds/Spanish-learning-project/CLAUDE.md`
- **Product Vision**: `/Users/brettreynolds/Spanish-learning-project/idea.md`
- **Repository Guidelines**: `/Users/brettreynolds/Spanish-learning-project/AGENTS.md`

## License

This project is part of the Spanish Language Learning Coach system.
