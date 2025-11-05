# Data Sources & Provenance

This document provides complete citations and licensing information for all third-party data resources used in this project.

---

## Frequency & Psycholinguistic Data

### SUBTLEX-ESP
**Word frequency database based on Spanish film subtitles**

**Citation**:
> Cuetos, F., Glez-Nosti, M., Barbón, A., & Brysbaert, M. (2011). SUBTLEX-ESP: Spanish word frequencies based on film subtitles. *Psicológica*, 32, 133–143.

**Usage**: Zipf scores and per-million frequency rates for Spanish lexemes and word forms.

**License**: Available for research purposes. See original publication for terms.

**Location**: `data/frequency/normalized/subtlex.tsv` (processed from `corpora-frequency/SUBTLEX-ESP.xlsx`)

---

### Multilex
**Aggregated Spanish word frequency norms from multiple corpora**

**Citation**:
> Duchon, A., Perea, M., Sebastián-Gallés, N., Martí, A., & Carreiras, M. (2013). EsPal: One-stop shopping for Spanish word properties. *Behavior Research Methods*, 45(4), 1246–1258.

**Usage**: Log-frequency scores from the Multilex consortium aggregated release.

**License**: Available for research purposes through the EsPal database.

**Location**: `data/frequency/normalized/multilex_spanish_word_frequency.tsv`

---

### Corpus del Español
**Large reference corpus of contemporary Spanish (web and dialect samples)**

**Citation**:
> Davies, M. (2002–present). *Corpus del Español: Web/Dialects*. Available at http://www.corpusdelespanol.org

**Usage**: Lemma and word-form frequency distributions. Sample exports (every 10th entry from 200k forms, 40k lemmas).

**License**: Use in accordance with corpus terms of service.

**Location**:
- `data/frequency/normalized/spanish_lemmas_40k.tsv`
- `data/frequency/normalized/spanish_forms_40k.tsv`
- `data/frequency/normalized/spanish_forms_200k.tsv`

---

### GPT-Derived Estimates
**AI-estimated familiarity and affective ratings**

**Source**: Custom datasets provided by project owner.

**Citation**: When reusing, cite the original spreadsheet files:
- `GPT familiarity estimates Spanish words.xlsx`
- `GPT_estimates_valence_arousal_concreteness.xlsx`

**Usage**:
- Familiarity ratings (1-7 scale)
- Valence, arousal, and concreteness ratings
- Used to inform vocabulary selection and difficulty calibration

**License**: Project-internal data. Not for redistribution without permission.

**Location**:
- `data/frequency/normalized/gpt familiarity estimates spanish words.tsv`
- `data/frequency/normalized/gpt_estimates_valence_arousal_concreteness.tsv`

---

## Corpus Resources

### PRESEEA
**Proyecto para el Estudio Sociolingüístico del Español de España y América**

**Description**: Oral Spanish transcripts from sociolinguistic interviews across 15+ Spanish-speaking cities.

**Citation**:
> Proyecto para el Estudio Sociolingüístico del Español de España y América (PRESEEA). Available at http://preseea.linguas.net

**Usage**:
- Authentic conversational examples for Knowledge Graph nodes
- Natural language sampling for exercise generation
- Speaker demographic filtering for targeted examples

**License**: Respect project licensing terms when using derived files.

**Location**:
- Raw transcripts: `data/frequency/preseea/`
- Processed data: `data/frequency/preseea/processed/`

---

## Curriculum Standards

### CEFR (Common European Framework of Reference for Languages)

**Citation**:
> Council of Europe. (2020). *Common European Framework of Reference for Languages: Learning, Teaching, Assessment – Companion Volume*. Available at https://www.coe.int/lang-cefr

**Usage**:
- CEFR levels (A1, A2, B1, B2) for node alignment
- Can-do descriptors for communicative competences
- Assessment criteria (grammatical control, coherence, pronunciation)

**License**: Freely available for educational and research use.

---

### PCIC (Plan Curricular del Instituto Cervantes)

**Citation**:
> Instituto Cervantes. (2006). *Plan Curricular del Instituto Cervantes: Niveles de referencia para el español*. Madrid: Biblioteca Nueva.

**Usage**:
- Grammar inventory for Spanish (constructions, morphology)
- Functional notions and vocabulary themes
- Discourse and pragmatic markers

**License**: Available through Instituto Cervantes. Used for educational reference.

---

## Linguistic Frameworks

### Four Strands Framework

**Citation**:
> Nation, I.S.P. (2007). The four strands. *Innovation in Language Learning and Teaching*, 1(1), 2–13.

**Usage**: Session planning with 25% distribution across meaning-focused input, meaning-focused output, language-focused learning, and fluency development.

---

### FSRS (Free Spaced Repetition Scheduler)

**Citation**:
> Ye, J., et al. (2024). Optimizing Spaced Repetition Schedule by Capturing the Dynamics of Memory. *IEEE Transactions on Neural Networks and Learning Systems*.

**Reference**: https://github.com/open-spaced-repetition/fsrs4anki/wiki/ABC-of-FSRS

**Usage**: Review scheduling based on stability and difficulty parameters.

---

## Reproducibility

All frequency databases and processed corpus files can be regenerated from source data:

```bash
# Build frequency index
python scripts/build_frequency_index.py

# Process PRESEEA transcripts
python scripts/process_preseea.py data/frequency/preseea data/frequency/preseea/processed

# Build Knowledge Graph
python kg/build.py kg/seed kg.sqlite
```

---

## Licensing Summary

| Resource | License Type | Redistribution |
|----------|-------------|----------------|
| SUBTLEX-ESP | Research use | Contact authors |
| Multilex | Research use | Via EsPal database |
| Corpus del Español | Terms of service | See corpus website |
| GPT estimates | Project-internal | Not permitted |
| PRESEEA | Project terms | See PRESEEA website |
| CEFR | Educational/research | Freely available |
| PCIC | Educational reference | Via Instituto Cervantes |

**Note**: This project is for personal exploration and research. If adapting for commercial use, verify licensing terms.

---

Last updated: 2025-11-05
