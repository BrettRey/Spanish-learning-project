#!/usr/bin/env python3
"""
Sample turns from the processed PRESEEA transcripts.

Usage examples:
    python tools/preseea_sampler.py --contains "disciplina" --limit 5
    python tools/preseea_sampler.py --subcorpus Nueva --speaker I --city "Nueva York"
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "frequency" / "preseea" / "processed"
METADATA_PATH = PROCESSED_DIR / "metadata.tsv"
TURNS_PATH = PROCESSED_DIR / "turns.tsv"


def load_metadata() -> Dict[str, Dict[str, str]]:
    metadata: Dict[str, Dict[str, str]] = {}
    if not METADATA_PATH.exists():
        return metadata
    with METADATA_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            metadata[row["file"]] = row
    return metadata


def iter_turns() -> Iterable[Dict[str, str]]:
    if not TURNS_PATH.exists():
        return []
    with TURNS_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            yield row


def lower_or_empty(value: str | None) -> str:
    return (value or "").lower()


def matches_filters(
    row: Dict[str, str],
    meta: Dict[str, str],
    args: argparse.Namespace,
    contains_regex: List[re.Pattern],
) -> bool:
    if args.speaker and row["speaker"].upper() not in args.speaker:
        return False

    clean = lower_or_empty(row.get("clean"))
    if args.contains:
        for needle in args.contains:
            if needle not in clean:
                return False

    for pattern in contains_regex:
        if not pattern.search(clean):
            return False

    if args.min_tokens or args.max_tokens:
        token_count = len(clean.split())
        if args.min_tokens and token_count < args.min_tokens:
            return False
        if args.max_tokens and token_count > args.max_tokens:
            return False

    if args.subcorpus:
        subcorpus = lower_or_empty(meta.get("subcorpus"))
        if not any(sc in subcorpus for sc in args.subcorpus):
            return False

    if args.city:
        city = lower_or_empty(meta.get("city"))
        if not any(city_filter in city for city_filter in args.city):
            return False

    if args.country:
        country = lower_or_empty(meta.get("country"))
        if not any(country_filter in country for country_filter in args.country):
            return False

    return True


def format_output(
    row: Dict[str, str],
    meta: Dict[str, str],
    args: argparse.Namespace,
) -> str:
    header = f"{row['file']}#T{row['turn_index']} [{row['speaker']}]"
    text = row["clean"] if not args.show_raw else row["raw"]
    lines = [f"{header} {text}"]

    if args.show_meta:
        interesting_keys = [
            "subcorpus",
            "city",
            "country",
            "participant_age",
            "participant_age_group",
            "participant_sex",
            "interviewer_id",
        ]
        meta_pairs = [
            f"{key}={meta.get(key, '')}"
            for key in interesting_keys
            if meta.get(key)
        ]
        if meta_pairs:
            lines.append("    " + "; ".join(meta_pairs))

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample turns from PRESEEA transcripts.")
    parser.add_argument("--subcorpus", nargs="+", help="Filter by subcorpus (case-insensitive substring).")
    parser.add_argument("--city", nargs="+", help="Filter by city (case-insensitive substring).")
    parser.add_argument("--country", nargs="+", help="Filter by country (case-insensitive substring).")
    parser.add_argument("--speaker", nargs="+", help="Filter by speaker codes (e.g., E, I).")
    parser.add_argument("--contains", nargs="+", help="Require all substrings in the clean text (case-insensitive).")
    parser.add_argument(
        "--regex",
        nargs="+",
        help="Require all regular expressions (applied to clean text).",
    )
    parser.add_argument("--min-tokens", type=int, help="Minimum number of tokens in clean text.")
    parser.add_argument("--max-tokens", type=int, help="Maximum number of tokens in clean text.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results to display.")
    parser.add_argument("--show-meta", action="store_true", help="Print metadata summary alongside each turn.")
    parser.add_argument("--show-raw", action="store_true", help="Display raw text instead of cleaned text.")
    return parser.parse_args()


def main() -> None:
    if not TURNS_PATH.exists():
        raise SystemExit("No turns TSV found. Run scripts/process_preseea.py first.")

    args = parse_args()
    metadata = load_metadata()

    regex_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in (args.regex or [])]
    results = 0

    for turn in iter_turns():
        meta = metadata.get(turn["file"], {})
        if matches_filters(turn, meta, args, regex_patterns):
            print(format_output(turn, meta, args))
            print()
            results += 1
            if args.limit and results >= args.limit:
                break

    if results == 0:
        print("No turns matched the given filters.")


if __name__ == "__main__":
    main()
