# Frequency Resources

Generated assets for Spanish lexical frequency, familiarity, and affective norms.

## Source Files
Place original XLSX/TXT datasets in the repository root (already provided):
- `corpora-frequency/SUBTLEX-ESP.xlsx` — SUBTLEX-ESP word frequencies (Cuetos, Glez-Nosti, Barbón & Brysbaert, 2011).
- `corpora-frequency/Multilex_Spanish_word_frequency.xlsx` — Multilex log-frequency norms (Duchon et al., 2013 / Multilex consortium).
- `corpora-frequency/GPT familiarity estimates Spanish words.xlsx` & `corpora-frequency/GPT_estimates_valence_arousal_concreteness.xlsx` — familiarity and affective estimates supplied in the project brief.
- `span_40k_lemmas.txt`, `span_40k_forms.txt`, `span_200k.txt` — sample exports (every 10th entry) from the Corpus del Español (Mark Davies, www.corpusdelespanol.org). Use in accordance with the corpus terms of use.

## Normalization Script
Run:
```bash
python scripts/build_frequency_index.py
```
This converts the raw data into UTF-8 TSV tables under `data/frequency/normalized/` and builds a consolidated SQLite database at `data/frequency/frequency.sqlite`.

### PRESEEA transcripts
```bash
python scripts/process_preseea.py
```
Parses the PRESEEA interview files in `data/frequency/preseea/` and saves structured metadata and turn-level TSVs to `data/frequency/preseea/processed/`.

## Quick Lookup
Use:
```bash
python tools/frequency_lookup.py palabra
```
The CLI returns matches across SUBTLEX, Multilex, 40k lemma/form lists, and GPT-derived familiarity/affect scores.

### PRESEEA Sampling
```bash
python tools/preseea_sampler.py --contains "disciplina" --limit 5 --show-meta
```
Filter turns by subcorpus, city, speaker role, substrings, or regular expressions to harvest natural conversational snippets for examples and rubrics.

## Output Tables
- `subtlex.tsv`: word, frequency count, per-million rate, log frequency.
- `multilex_spanish_word_frequency.tsv`: Multilex log frequency scores.
- `gpt familiarity estimates spanish words.tsv`: familiarity ratings.
- `gpt_estimates_valence_arousal_concreteness.tsv`: affective norms.
- `spanish_lemmas_40k.tsv`: lemma-level counts from Corpus del Español.
- `spanish_forms_40k.tsv`: word-form distribution within lemmas.
- `spanish_forms_200k.tsv`: top 200k forms with counts.
- `preseea/processed/metadata.tsv`: transcript-level metadata from PRESEEA interviews.
- `preseea/processed/turns.tsv`: speaker turns with raw and cleaned text for each transcript.

## Citations
- **SUBTLEX-ESP**: Cuetos, F., Glez-Nosti, M., Barbón, A., & Brysbaert, M. (2011). *SUBTLEX-ESP: Spanish word frequencies based on film subtitles.* Psicológica, 32, 133–143.
- **Multilex**: Duchon, A., Perea, M., Sebastián-Gallés, N., Martí, A., & Carreiras, M. (2013). *EsPal: One-stop shopping for Spanish word properties.* Behavior Research Methods, 45(4), 1246–1258. (Multilex aggregated release.)
- **Corpus del Español samples**: Davies, M. (2002–present). *Corpus del Español: Web/Dialects.* http://www.corpusdelespanol.org
- **GPT familiarity/affect estimates**: Provided by project owner; cite the internal spreadsheet name when reusing (`GPT familiarity estimates Spanish words.xlsx`, `GPT_estimates_valence_arousal_concreteness.xlsx`).
- **PRESEEA transcripts**: Proyecto para el Estudio Sociolingüístico del Español de España y América (PRESEEA). http://preseea.linguas.net (respect project licensing when using the derived files).
