# Knowledge Graph (KG)

This directory contains the knowledge graph infrastructure for the Spanish language learning system. The knowledge graph tracks linguistic constructs (lexemes, constructions, morphology, can-do statements) and their relationships.

## Directory Structure

```
kg/
├── README.md          # This file
├── build.py           # Compiler script (YAML → SQLite)
├── seed/              # YAML source files defining nodes
│   ├── present_indicative.yaml
│   ├── subjunctive_present.yaml
│   ├── verb_tener.yaml
│   └── ...
└── kg.sqlite          # Compiled graph database (generated)
```

## Node Types

The knowledge graph supports the following node types:

- **Lexeme**: Individual words or expressions (e.g., "tener", "gustar")
- **Construction**: Grammatical patterns (e.g., present subjunctive, present indicative)
- **Morph**: Morphological elements (e.g., verb endings, pronouns)
- **CanDo**: CEFR-aligned can-do statements (e.g., "express doubt at B1 level")
- **Function**: Communicative functions
- **Topic**: Subject matter domains
- **Script**: Situational scripts
- **PhonologyItem**: Pronunciation features

## Edge Types

Relationships between nodes:

- **prerequisite_of**: Node A must be learned before Node B
- **realizes**: Construction/lexeme realizes a can-do statement
- **contrasts_with**: Two items that learners often confuse
- **depends_on**: Softer dependency than prerequisite
- **practice_with**: Items that work well together in exercises
- **addresses_error**: Links constructions to common learner errors

## Node Schema

Each YAML file in `seed/` defines a single node with the following structure:

```yaml
id: node.type.identifier           # Unique identifier
type: NodeType                      # One of the types above
label: Human-readable name          # Display name
prerequisites: [id1, id2]           # List of prerequisite node IDs
can_do: [cando_id1, cando_id2]     # Can-do statements this realizes
diagnostics:                        # Linguistic diagnostics
  form: "Morphological form"
  function: "Semantic/pragmatic function"
  usage_constraints: "When/how to use"
cefr_level: A1|A2|B1|B2|C1|C2      # CEFR alignment
prompts:                            # Exercise prompts
  - "Prompt 1"
  - "Prompt 2"
examples:                           # (Optional) Usage examples
  - "Example sentence 1"
  - "Example sentence 2"
corpus_examples:                    # (Recommended) Authentic citations
  - text: "Transcript excerpt or corpus sentence"
    source: "preseea/ALCA_H11_037.txt#T74"
    notes: "Optional context information"
frequency:                          # Lexeme frequency metadata (Zipf scores, etc.)
  family_zipf: 4.78
  corpus: "Corpus del Español (Davies, 2020)"
metadata:
  source:
    - "CEFR Companion Volume, B1 Spoken Production"
    - "Plan Curricular Instituto Cervantes, Nivel B1"
contrasts_with: [id1, id2]         # (Optional) Contrastive items
practice_with: [id1, id2]          # (Optional) Practice companions
```

### Field Guidelines

- **metadata.source** (required): cite every external reference (CEFR descriptors, textbooks, corpora). Use descriptive strings so downstream agents can trace provenance.
- **corpus_examples** (recommended for communicative nodes): include real-world utterances with `text` and `source`. The `source` should reference the corpus and turn ID, e.g., `preseea/NYOC_H11_001.txt#T132`. Add `notes` if additional context is needed.
- **frequency** (required for Lexeme nodes): provide word-family Zipf scores and the corpus or list used. Additional keys (e.g., familiarity, affect) may be added when available.
- **examples**: keep short, pedagogically clear sentences. Use `corpus_examples` for longer authentic snippets.

## Building the Knowledge Graph

### Prerequisites

Ensure you have Python 3.11+ and the required dependencies:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (if not already installed)
pip install pyyaml
```

### Running the Builder

```bash
# From project root
python kg/build.py kg/seed kg.sqlite
```

This will:
1. Read all YAML files from `kg/seed/`
2. Validate node structure
3. Create `kg.sqlite` with nodes and edges tables
4. Insert all nodes and their relationships

### Output

The script creates a SQLite database with two main tables:

**nodes**
- `id` (TEXT, PRIMARY KEY): Unique node identifier
- `type` (TEXT): Node type (Lexeme, Construction, etc.)
- `label` (TEXT): Human-readable label
- `data_json` (TEXT): Full node data as JSON

**edges**
- `from_id` (TEXT): Source node ID
- `to_id` (TEXT): Target node ID
- `type` (TEXT): Edge relationship type

## Testing the Build

### Manual Testing

```bash
# Build the database
python kg/build.py kg/seed kg.sqlite

# Verify it was created
ls -lh kg.sqlite

# Query the database
sqlite3 kg.sqlite "SELECT id, type, label FROM nodes;"
sqlite3 kg.sqlite "SELECT * FROM edges;"
```

### Verify Node Count

```bash
# Count nodes by type
sqlite3 kg.sqlite "SELECT type, COUNT(*) FROM nodes GROUP BY type;"
```

### Check Relationships

```bash
# View all prerequisite relationships
sqlite3 kg.sqlite "SELECT from_id, to_id FROM edges WHERE type = 'prerequisite_of';"

# Find nodes with no prerequisites (entry points)
sqlite3 kg.sqlite "
  SELECT id, type, label
  FROM nodes
  WHERE id NOT IN (SELECT to_id FROM edges WHERE type = 'prerequisite_of')
  ORDER BY type;
"
```

### Inspect Specific Nodes

```bash
# View full data for a specific node
sqlite3 kg.sqlite "SELECT data_json FROM nodes WHERE id = 'constr.es.subjunctive_present';" | jq .
```

## Example Nodes

The seed directory currently contains 10 example nodes covering A1-B1 Spanish:

1. **constr.es.present_indicative**: Basic present tense construction
2. **constr.es.subjunctive_present**: Present subjunctive construction
3. **morph.es.regular_verb_endings**: Regular verb conjugation endings
4. **morph.es.subjunctive_endings**: Subjunctive mood endings
5. **morph.es.indirect_object_pronouns**: Indirect object pronoun system
6. **lex.es.tener**: "to have" verb with idioms
7. **lex.es.querer**: "to want" verb (triggers subjunctive)
8. **lex.es.gustar**: "to like" verb (reverse construction)
9. **cando.es.express_doubt_B1**: B1-level epistemic expressions
10. **cando.es.express_desire_A2**: A2-level desire expressions

### Prerequisite Chain Example

```
morph.es.regular_verb_endings (A1, no prerequisites)
  ↓
constr.es.present_indicative (A1)
  ↓
morph.es.subjunctive_endings (A2)
  ↓
constr.es.subjunctive_present (B1)
  ↓
cando.es.express_doubt_B1 (B1)
```

## Extending the Knowledge Graph

### Adding New Nodes

1. Create a new YAML file in `kg/seed/` following the schema above
2. Ensure the `id` follows the naming convention: `type.lang.identifier`
3. Reference existing node IDs in `prerequisites`, `can_do`, etc.
4. Run `build.py` to regenerate `kg.sqlite`

### Node ID Conventions

- Constructions: `constr.es.<name>`
- Lexemes: `lex.es.<word>`
- Morphology: `morph.es.<feature>`
- Can-Do: `cando.es.<description>_<level>`
- Functions: `func.es.<name>`
- Topics: `topic.es.<domain>`

### Validation

The builder validates:
- Required fields (`id`, `type`, `label`)
- YAML syntax
- Unique node IDs (duplicates are replaced)

It does NOT currently validate:
- Edge target existence (dangling references)
- CEFR level consistency
- Prerequisite cycles

Run `python scripts/validate_kg.py` to check additional style requirements, including `metadata.source`, lexeme frequency metadata, and corpus example formatting.

## Integration with Other Components

### MCP KG Server

The `mcp_servers/kg_server` module will query this database to:
- Find frontier nodes (prerequisites satisfied, not yet mastered)
- Retrieve prompts for exercises
- Log learner evidence to track mastery

### Learner State

The `state/mastery.sqlite` database links SRS cards to KG node IDs, enabling:
- Spaced repetition scheduling
- Progress tracking through the curriculum
- Personalized next-best-action recommendations

## Troubleshooting

### "No module named 'yaml'"

Install PyYAML:
```bash
pip install pyyaml
```

### "Missing required fields"

Ensure each YAML file has `id`, `type`, and `label` fields.

### Edge Target Not Found

The builder allows dangling references (edges pointing to non-existent nodes) for flexibility during development. The MCP server should handle missing references gracefully.

## Future Enhancements

- [ ] Validate edge targets exist in the graph
- [ ] Detect prerequisite cycles
- [ ] Generate graphical visualization of the knowledge graph
- [ ] Add support for importing from other formats (JSON, CSV)
- [ ] Version control for schema evolution
- [ ] Migration system for database schema changes
