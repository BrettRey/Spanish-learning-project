#!/usr/bin/env python3
"""
Process PRESEEA transcript files into normalized TSV outputs.

Input  : data/frequency/preseea/*.txt  (original PRESEEA transcripts)
Output : data/frequency/preseea/processed/
           ├── metadata.tsv       (one row per transcript)
           └── turns.tsv          (one row per conversational turn)

Usage:
    python scripts/process_preseea.py

The script uses only the Python standard library. All turns retain the raw
transcript line plus a lightly cleaned variant with annotation tags stripped.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
PRESEEA_DIR = BASE_DIR / "data" / "frequency" / "preseea"
OUTPUT_DIR = PRESEEA_DIR / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TAG_RE = re.compile(r"<[^>]+>")
TURN_RE = re.compile(r"^([A-ZÁÉÍÓÚÜÑ]{1,3}):\s*(.*)")


def clean_text(text: str) -> str:
    """Remove inline markup such as <ininteligible/> and collapse whitespace."""
    text = TAG_RE.sub("", text)
    return " ".join(text.split())


def parse_metadata(content: str) -> Dict[str, str]:
    metadata: Dict[str, str] = {}

    match = re.search(r'<Trans[^>]*audio_filename="([^"]+)"', content)
    if match:
        metadata["audio_filename"] = match.group(1)

    match = re.search(r'<Corpus[^>]*subcorpus="([^"]+)"', content)
    if match:
        metadata["subcorpus"] = match.group(1)

    match = re.search(r'<Corpus[^>]*ciudad="([^"]+)"', content)
    if match:
        metadata["city"] = match.group(1)

    match = re.search(r'<Corpus[^>]*pais="([^"]+)"', content)
    if match:
        metadata["country"] = match.group(1)

    # Participant metadata (first interviewer / interviewee entries)
    speaker_matches = re.findall(
        r'<Hablante[^>]*nombre="([^"]+)"[^>]*codigo_hab="([A-Z])"[^>]*sexo="([^"]+)"[^>]*grupo_edad="([^"]+)"[^>]*edad="([^"]+)"[^>]*nivel_edu="([^"]+)"',
        content,
    )
    for name, code, sex, age_group, age, edu in speaker_matches:
        key_prefix = "interviewer" if code.upper() == "E" else "participant"
        metadata[f"{key_prefix}_id"] = name
        metadata[f"{key_prefix}_sex"] = sex
        metadata[f"{key_prefix}_age_group"] = age_group
        metadata[f"{key_prefix}_age"] = age
        metadata[f"{key_prefix}_education"] = edu

    return metadata


def extract_turns(path: Path, content: str) -> List[Dict[str, str]]:
    turns: List[Dict[str, str]] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("<"):
            continue

        match = TURN_RE.match(line)
        if not match:
            continue

        speaker, raw_text = match.groups()
        turns.append(
            {
                "file": path.name,
                "speaker": speaker,
                "raw": raw_text,
                "clean": clean_text(raw_text),
            }
        )
    return turns


def read_text_with_fallback(path: Path) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Unable to decode {path}")


def process_file(path: Path):
    content = read_text_with_fallback(path)
    metadata = parse_metadata(content)
    metadata["file"] = path.name
    turns = extract_turns(path, content)
    return metadata, turns


def main() -> None:
    files = sorted(PRESEEA_DIR.glob("*.txt"))
    if not files:
        raise SystemExit("No PRESEEA transcripts found.")

    metadata_rows: List[Dict[str, str]] = []
    turn_rows: List[Dict[str, str]] = []

    for file_path in files:
        metadata, turns = process_file(file_path)
        metadata_rows.append(metadata)
        turn_rows.extend(turns)

    metadata_fields = sorted({key for row in metadata_rows for key in row.keys()})
    with (OUTPUT_DIR / "metadata.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=metadata_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(metadata_rows)

    with (OUTPUT_DIR / "turns.tsv").open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["file", "turn_index", "speaker", "raw", "clean"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for idx, row in enumerate(turn_rows, start=1):
            writer.writerow(
                {
                    "file": row["file"],
                    "turn_index": idx,
                    "speaker": row["speaker"],
                    "raw": row["raw"],
                    "clean": row["clean"],
                }
            )

    print(
        f"Processed {len(files)} transcripts -> "
        f"{OUTPUT_DIR / 'metadata.tsv'} and {OUTPUT_DIR / 'turns.tsv'}"
    )


if __name__ == "__main__":
    main()
