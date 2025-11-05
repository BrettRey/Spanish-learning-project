#!/usr/bin/env python3
"""
Normalize local Spanish frequency resources into tabular TSV files and a SQLite index.

This script relies only on the Python standard library so it can run inside the
current sandboxed environment. It processes the following inputs (if present):

- corpora-frequency/SUBTLEX-ESP.xlsx
- corpora-frequency/Multilex_Spanish_word_frequency.xlsx
- corpora-frequency/GPT familiarity estimates Spanish words.xlsx
- corpora-frequency/GPT_estimates_valence_arousal_concreteness.xlsx
- span_40k_lemmas.txt
- span_40k_forms.txt
- span_200k.txt

Outputs are written to:
    data/frequency/normalized/*.tsv
and a consolidated SQLite database at:
    data/frequency/frequency.sqlite
"""

from __future__ import annotations

import csv
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "corpora-frequency"
RAW_TXT_DIR = BASE_DIR
OUTPUT_DIR = BASE_DIR / "data" / "frequency" / "normalized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_PATH = BASE_DIR / "data" / "frequency" / "frequency.sqlite"


def chunk_subtlex_columns(row: list[str]) -> list[dict[str, str]]:
    """Split a SUBTLEX row into blocks of four columns (Word, Freq count, etc.)."""
    blocks: list[dict[str, str]] = []
    headers = ["Word", "Freq. count", "Freq. per million", "Log freq."]

    i = 0
    while i < len(row):
        # Skip blank separators
        if not row[i]:
            i += 1
            continue

        chunk = row[i : i + 4]
        if len(chunk) < 4 or not chunk[0]:
            break

        entry = dict(zip(headers, chunk))
        blocks.append(entry)
        i += 4

    return blocks


def parse_xlsx_table(path: Path) -> list[list[str]]:
    """
    Read the first worksheet of an XLSX file and return rows as lists of cell values.
    Only string and numeric types are supported; formula results are not evaluated.
    """
    if not path.exists():
        return []

    with zipfile.ZipFile(path) as zf:
        sheet = ET.parse(zf.open("xl/worksheets/sheet1.xml")).getroot()
        ns = {"a": sheet.tag.split("}")[0].strip("{")}

        # Load shared strings table (if any)
        shared_strings: list[str] = []
        try:
            shared_root = ET.parse(zf.open("xl/sharedStrings.xml")).getroot()
            ns_shared = {"a": shared_root.tag.split("}")[0].strip("{")}
            for si in shared_root.findall("a:si", ns_shared):
                text_parts = [t.text or "" for t in si.findall(".//a:t", ns_shared)]
                shared_strings.append("".join(text_parts))
        except KeyError:
            shared_root = None

        def col_index(cell_ref: str) -> int:
            idx = 0
            for char in cell_ref:
                if char.isdigit():
                    break
                idx = idx * 26 + (ord(char.upper()) - ord("A") + 1)
            return idx - 1

        rows: list[dict[int, str]] = []
        for row in sheet.find("a:sheetData", ns).findall("a:row", ns):
            row_cells: dict[int, str] = {}
            for c in row.findall("a:c", ns):
                cell_ref = c.attrib.get("r")
                if cell_ref is None:
                    continue
                idx = col_index(cell_ref)
                cell_type = c.attrib.get("t")
                value = ""

                v = c.find("a:v", ns)
                if v is not None:
                    raw = v.text or ""
                    if cell_type == "s":
                        value = shared_strings[int(raw)] if shared_strings else raw
                    else:
                        value = raw
                else:
                    inline = c.find("a:is", ns)
                    if inline is not None:
                        parts = [t.text or "" for t in inline.findall(".//a:t", ns)]
                        value = "".join(parts)

                row_cells[idx] = value.strip()

            if row_cells:
                rows.append(row_cells)

        if not rows:
            return []

        max_col = max(max(r.keys()) for r in rows)
        matrix: list[list[str]] = []
        for row_cells in rows:
            row = [""] * (max_col + 1)
            for idx, value in row_cells.items():
                if 0 <= idx < len(row):
                    row[idx] = value
            matrix.append(row)

        return matrix


def normalize_subtlex() -> Path | None:
    xlsx_path = RAW_DIR / "SUBTLEX-ESP.xlsx"
    if not xlsx_path.exists():
        return None

    rows = parse_xlsx_table(xlsx_path)
    if not rows:
        return None

    normalized_rows: list[list[str]] = [["word", "freq_count", "freq_per_million", "log_freq"]]

    # Start after header row
    for row in rows[1:]:
        for block in chunk_subtlex_columns(row):
            word = block.get("Word", "").strip()
            if not word:
                continue
            normalized_rows.append(
                [
                    word,
                    block.get("Freq. count", "").strip(),
                    block.get("Freq. per million", "").strip(),
                    block.get("Log freq.", "").strip(),
                ]
            )

    output_path = OUTPUT_DIR / "subtlex.tsv"
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(normalized_rows)

    return output_path


def copy_simple_xlsx(stem: str) -> Path | None:
    xlsx_path = RAW_DIR / f"{stem}.xlsx"
    if not xlsx_path.exists():
        return None

    rows = parse_xlsx_table(xlsx_path)
    if not rows:
        return None

    output_path = OUTPUT_DIR / f"{stem.lower()}.tsv"
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(rows)
    return output_path


def normalize_spanish_frequency_text(filename: str, output_name: str) -> Path | None:
    source_path = RAW_TXT_DIR / filename
    if not source_path.exists():
        return None

    output_path = OUTPUT_DIR / output_name
    text = None
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            text = source_path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise UnicodeError(f"Unable to decode {filename} with utf-8/latin-1/cp1252")

    with output_path.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.writer(dst, delimiter="\t")
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("*") or stripped.startswith("---"):
                continue
            if stripped.startswith("ID"):
                writer.writerow(stripped.split("\t"))
                continue
            writer.writerow(stripped.split("\t"))
    return output_path


def write_sqlite_index(paths: dict[str, Path]) -> None:
    if SQLITE_PATH.exists():
        SQLITE_PATH.unlink()

    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()

    def load_tsv(table: str, path: Path) -> None:
        if path is None or not path.exists():
            return

        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader, None)
            if not header:
                return

            columns = ", ".join(f'"{h}" TEXT' for h in header)
            placeholders = ", ".join("?" for _ in header)
            cur.execute(f'DROP TABLE IF EXISTS "{table}"')
            cur.execute(f'CREATE TABLE "{table}" ({columns})')
            cur.executemany(
                f'INSERT INTO "{table}" VALUES ({placeholders})',
                reader,
            )

    load_tsv("subtlex", paths.get("subtlex"))
    load_tsv("multilex", paths.get("multilex"))
    load_tsv("gpt_familiarity", paths.get("gpt_familiarity"))
    load_tsv("gpt_affect", paths.get("gpt_affect"))
    load_tsv("lemma40k", paths.get("lemma40k"))
    load_tsv("form40k", paths.get("form40k"))
    load_tsv("form200k", paths.get("form200k"))

    conn.commit()
    conn.close()


def main() -> None:
    paths: dict[str, Path] = {}

    paths["subtlex"] = normalize_subtlex()
    paths["multilex"] = copy_simple_xlsx("Multilex_Spanish_word_frequency")
    paths["gpt_familiarity"] = copy_simple_xlsx("GPT familiarity estimates Spanish words")
    paths["gpt_affect"] = copy_simple_xlsx("GPT_estimates_valence_arousal_concreteness")

    paths["lemma40k"] = normalize_spanish_frequency_text("span_40k_lemmas.txt", "spanish_lemmas_40k.tsv")
    paths["form40k"] = normalize_spanish_frequency_text("span_40k_forms.txt", "spanish_forms_40k.tsv")
    paths["form200k"] = normalize_spanish_frequency_text("span_200k.txt", "spanish_forms_200k.tsv")

    write_sqlite_index(paths)

    print("Frequency resources normalized:")
    for key, value in paths.items():
        if value is None:
            continue
        print(f" - {key}: {value.relative_to(BASE_DIR)}")
    print(f"SQLite index: {SQLITE_PATH.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
