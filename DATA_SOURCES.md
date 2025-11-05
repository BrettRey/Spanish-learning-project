# Data Sources & Licenses

This document describes all third-party data sources used in the Spanish Learning Project, their provenance, licenses, and how to obtain them.

## Policy

**No third-party data is committed to this repository.** All corpus data, frequency lists, and generated databases must be:
1. Downloaded from original sources or provided separately
2. Rebuilt locally via scripts
3. Acknowledged with proper citations

See `.gitignore` for the artifact policy.

---

## Frequency Data Sources

### SUBTLEX-ESP
**Description**: Spanish word frequencies based on film subtitles (71 million words)

**Citation**:
> Cuetos, F., Glez-Nosti, M., Barbón, A., & Brysbaert, M. (2011). *SUBTLEX-ESP: Spanish word frequencies based on film subtitles.* Psicológica, 32, 133–143.

**License**: Research and educational use permitted with citation

**Format**: Excel file (`SUBTLEX-ESP.xlsx`)

**How to obtain**:
- Available from: http://www.bcbl.eu/databases/subtlex-esp/
- Or: Request from research authors
- Place in: `data/frequency/SUBTLEX-ESP.xlsx` (not tracked)

**Processing**: `python scripts/build_frequency_index.py` → `data/frequency/normalized/subtlex.tsv`

---

### Multilex Spanish Word Frequency
**Description**: Aggregated word frequency norms from multiple Spanish corpora

**Citation**:
> Duchon, A., Perea, M., Sebastián-Gallés, N., Martí, A., & Carreiras, M. (2013). *EsPal: One-stop shopping for Spanish word properties.* Behavior Research Methods, 45(4), 1246–1258.

**License**: Research and educational use permitted with citation

**Format**: Excel file (`Multilex_Spanish_word_frequency.xlsx`)

**How to obtain**:
- Available from: http://www.bcbl.eu/databases/espal/ (EsPal database)
- Place in: `data/frequency/Multilex_Spanish_word_frequency.xlsx` (not tracked)

**Processing**: `python scripts/build_frequency_index.py` → `data/frequency/normalized/multilex_spanish_word_frequency.tsv`

---

### Corpus del Español
**Description**: Sample word frequencies from Mark Davies' Corpus del Español (Web/Dialects, 2 billion+ words)

**Citation**:
> Davies, M. (2002–present). *Corpus del Español: Web/Dialects.* http://www.corpusdelespanol.org

**License**: Sample exports for academic use; commercial use requires permission

**Format**:
- `span_40k_lemmas.txt` - Top 40,000 lemmas with counts
- `span_40k_forms.txt` - Word forms within lemmas
- `span_200k.txt` - Top 200,000 forms

**How to obtain**:
- Available from: http://www.corpusdelespanol.org
- These are sampled exports (every 10th entry) for reference
- Place in repository root (not tracked)

**Processing**: `python scripts/build_frequency_index.py` → normalized TSV files

**Terms of use**: Respect corpus licensing; cite Davies when using derived frequency data

---

### GPT Familiarity Estimates
**Description**: AI-estimated familiarity ratings for Spanish words

**Citation**: Internal project data; cite as "GPT familiarity estimates (Spanish Learning Project, 2025)"

**License**: Project-specific data; not for redistribution

**Format**: Excel files
- `GPT familiarity estimates Spanish words.xlsx`
- `GPT_estimates_valence_arousal_concreteness.xlsx` (valence, arousal, concreteness)

**How to obtain**: Provided separately by project owner

**Processing**: `python scripts/build_frequency_index.py` → normalized TSV files

---

## Corpus Data Sources

### PRESEEA (Proyecto para el Estudio Sociolingüístico del Español de España y América)
**Description**: Oral Spanish transcripts with sociolinguistic metadata (age, education, city, etc.)

**Citation**:
> Proyecto para el Estudio Sociolingüístico del Español de España y América (PRESEEA). http://preseea.linguas.net

**License**: Academic research license; requires registration and agreement to terms

**Format**: TXT files with metadata headers and speaker turn annotations

**How to obtain**:
1. Visit: http://preseea.linguas.net
2. Register for access
3. Download desired city corpora
4. Place in: `data/frequency/preseea/` (not tracked)

**Processing**:
```bash
python scripts/process_preseea.py data/frequency/preseea data/frequency/preseea/processed
```

**Output**:
- `data/frequency/preseea/processed/metadata.tsv` - Transcript metadata
- `data/frequency/preseea/processed/turns.tsv` - Speaker turns with cleaned text

**Terms of use**:
- Academic research only
- Must cite PRESEEA in publications
- Cannot redistribute raw transcripts
- This project only tracks processing scripts, not corpus files

---

## Knowledge Graph Sources

### YAML Node Definitions
**Description**: Hand-authored linguistic node definitions (lexemes, constructions, morphology)

**License**: MIT (part of this project)

**Format**: YAML files in `kg/seed/*.yaml`

**Citations**: Individual nodes cite:
- CEFR descriptors (Council of Europe)
- PCIC (Instituto Cervantes)
- RAE (Real Academia Española)
- Frequency data (see above)
- PRESEEA corpus examples (see above)

All node `source` fields include bibliographic references.

---

## Rebuilding All Data

### Quick Start
```bash
# 1. Obtain third-party data (see sections above)
# 2. Place files in appropriate locations
# 3. Run build scripts:

# Build knowledge graph from YAML
python kg/build.py kg/seed kg.sqlite

# Build frequency database from source files
python scripts/build_frequency_index.py

# Process PRESEEA transcripts
python scripts/process_preseea.py data/frequency/preseea data/frequency/preseea/processed
```

### Expected Output
- `kg.sqlite` (~140KB)
- `data/frequency/frequency.sqlite` (~80MB with all sources)
- `data/frequency/normalized/*.tsv` (UTF-8 normalized tables)
- `data/frequency/preseea/processed/*.tsv` (PRESEEA metadata and turns)

All generated databases are reproducible and not tracked in git.

---

## License Compliance Checklist

When using this project:

✅ **For personal learning**: All data sources permit educational use with citation

✅ **For research publications**:
- Cite all data sources used (see citations above)
- Follow PRESEEA terms (register, cite, no redistribution)
- Acknowledge SUBTLEX, Multilex, Corpus del Español

✅ **For commercial use**:
- ⚠️  Contact corpus owners for permission (SUBTLEX, Multilex, PRESEEA)
- ⚠️  Corpus del Español requires commercial license
- ⚠️  GPT estimates are project-specific; do not redistribute

✅ **For redistribution**:
- Share scripts, not data
- Document how to obtain original sources
- Include this DATA_SOURCES.md with proper citations

---

## Questions & Updates

If you find broken links or licensing changes, please open an issue on GitHub.

**Last Updated**: 2025-11-05
