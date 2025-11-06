# Data Sources, Licenses, and Usage Constraints

This document tracks all external data sources used in the Spanish Learning Project.

## Summary Table

| Source | Type | License | Location |
|--------|------|---------|----------|
| SUBTLEX-ESP | Frequency | Academic research | `data/frequency/normalized/` |
| Multilex | Frequency | CC BY 4.0 | `data/frequency/normalized/` |
| GPT Familiarity | Psycholinguistic | Research | `data/frequency/normalized/` |
| Corpus del Español | Frequency | Academic research | `data/frequency/normalized/` |
| PRESEEA | Oral corpus | Academic research | `data/frequency/preseea/` |
| PCIC | CEFR descriptors | Public (educational) | `kg/descriptors/` |

## Detailed Sources

### SUBTLEX-ESP (Subtitle Frequencies)

**Citation**: Cuetos, F., et al. (2011). SUBTLEX-ESP: Spanish word frequencies based on film subtitles. _Psicológica_, 32(2), 133-143.

**License**: Academic research use

**Usage**: Zipf scores for lexeme difficulty calibration, frequency-based vocabulary selection

**Constraints**: For research and educational purposes; not for commercial redistribution

### Multilex (Word Family Frequencies)

**Citation**: Aguasvivas, J. A., et al. (2020). Multilex: A large-scale vocabulary database. _Behavior Research Methods_, 52(5), 1867-1882.

**License**: CC BY 4.0 (Creative Commons Attribution 4.0)

**Usage**: Word family frequency data, cross-regional frequency validation

**Constraints**: Must attribute original authors; share-alike if redistributed

**Attribution**: This project uses Multilex data under CC BY 4.0 license.

### GPT Familiarity Estimates

**Description**: AI-estimated familiarity, valence, arousal, concreteness for Spanish words

**License**: Research use

**Usage**: Familiarity ratings for vocabulary selection, affect dimensions, concreteness ratings for A1/A2

**Constraints**: For research/educational purposes; validate against human norms where possible

### Corpus del Español

**Citation**: Davies, Mark. (2002-) Corpus del Español. https://www.corpusdelespanol.org

**License**: Academic research use

**Usage**: Frequency validation, genre-specific frequency data

**Constraints**: For research/educational purposes; must cite original corpus

### PRESEEA (Oral Spanish Transcripts)

**Source**: Proyecto para el Estudio Sociolingüístico del Español de España y de América

**Citation**: PRESEEA. Corpus de español oral. Universidad de Alcalá. https://preseea.linguas.net

**License**: Academic research use

**Usage**: Authentic example sentences for KG nodes, natural language sampling, frequency validation

**Data**: 15+ cities with speaker metadata (age, education, socioeconomic status)

**Constraints**:
- For research/educational purposes
- Cannot redistribute full transcripts
- Can reference specific turns with citations
- Must respect speaker anonymity

**Processing**: `scripts/process_preseea.py`, `tools/preseea_sampler.py`

### PCIC (CEFR Descriptors)

**Source**: Instituto Cervantes. (2006). Plan Curricular del Instituto Cervantes.

**License**: Public (educational use)

**Usage**: Can-do descriptors for B1 content, CEFR alignment, assessment criteria

**Constraints**: Free for educational use; must cite Instituto Cervantes

## Usage Guidelines

### Allowed Uses
✅ Research & education
✅ Personal language learning  
✅ Anonymized examples for testing

### Restricted Uses
❌ Commercial use (requires separate permissions)
❌ Redistribution of full datasets
❌ Learner-identifiable data

### For Contributors

When adding new data sources:
1. Document in this file with full citation
2. Include license information
3. Note usage constraints
4. Specify location in project

### For Researchers

If publishing research using this project, cite:
1. This project (add project citation)
2. Individual data sources (use citations above)
3. FSRS Algorithm: Ye et al. (2024)

## Data Privacy

❌ **Never commit**:
- Learner-identifiable data
- Personal progress databases
- API keys or credentials

✅ **Do commit**:
- Anonymized example data
- Schema files and migrations

## Zipf Score Normalization

All frequency data normalized to log10 per billion words (1-7 scale):
- 7: Very common (top 10: "el", "de", "que")
- 4: Familiar (top 10,000)
- 1: Very rare

**Script**: `scripts/build_frequency_index.py`
**Output**: `data/frequency/frequency.sqlite`

## Validation

**Frequency lookup**: `python tools/frequency_lookup.py hablar`

**Corpus validation**: `python scripts/validate_kg.py`

## License Compliance Checklist

Before distribution:
- [ ] All sources documented with citations
- [ ] Usage constraints respected
- [ ] No full corpus redistributions
- [ ] Proper attributions in generated content
- [ ] No learner-identifiable data

---

**Last updated**: 2025-11-06
