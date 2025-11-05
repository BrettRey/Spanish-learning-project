#!/usr/bin/env python3
"""Validate KG seed files for metadata, frequency, and corpus example consistency."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
SEED_DIR = BASE_DIR / "kg" / "seed"


def load_yaml(path: Path) -> Dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except UnicodeDecodeError:
        return yaml.safe_load(path.read_text(encoding="latin-1")) or {}


def check_required_metadata(node: Dict, warnings: List[str], path: Path) -> None:
    sources = (node.get("metadata") or {}).get("source")
    if not sources or not isinstance(sources, list):
        warnings.append(f"{path.name}: missing metadata.source list")


def check_frequency(node: Dict, warnings: List[str], path: Path) -> None:
    if node.get("type") != "Lexeme":
        return
    freq = node.get("frequency")
    if not isinstance(freq, dict):
        warnings.append(f"{path.name}: lexeme missing frequency block")
        return
    if "family_zipf" not in freq:
        warnings.append(f"{path.name}: lexeme frequency missing family_zipf")
    if "corpus" not in freq:
        warnings.append(f"{path.name}: lexeme frequency missing corpus reference")


COMMUNICATIVE_TYPES = {
    "CanDo",
    "Function",
    "Construction",
    "PragmaticCue",
    "DiscourseMove",
    "Topic",
}


def check_corpus_examples(node: Dict, warnings: List[str], path: Path) -> None:
    node_type = node.get("type")
    corpus_examples = node.get("corpus_examples")
    if node_type in COMMUNICATIVE_TYPES:
        if not corpus_examples:
            warnings.append(f"{path.name}: expected corpus_examples for {node_type}")
            return
    if not corpus_examples:
        return
    if not isinstance(corpus_examples, list):
        warnings.append(f"{path.name}: corpus_examples must be a list")
        return
    for idx, entry in enumerate(corpus_examples):
        if not isinstance(entry, dict):
            warnings.append(f"{path.name}: corpus_examples[{idx}] must be a mapping")
            continue
        if not entry.get("text"):
            warnings.append(f"{path.name}: corpus_examples[{idx}] missing text")
        source = entry.get("source")
        if not source:
            warnings.append(f"{path.name}: corpus_examples[{idx}] missing source")
        elif not isinstance(source, str):
            warnings.append(f"{path.name}: corpus_examples[{idx}] source must be string")


def validate_node(path: Path) -> Tuple[List[str], Dict]:
    node = load_yaml(path)
    warnings: List[str] = []

    if not node:
        warnings.append(f"{path.name}: empty or invalid YAML")
        return warnings, node

    if "id" not in node:
        warnings.append(f"{path.name}: missing id")
    if "type" not in node:
        warnings.append(f"{path.name}: missing type")

    check_required_metadata(node, warnings, path)
    check_frequency(node, warnings, path)
    check_corpus_examples(node, warnings, path)

    return warnings, node


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate KG seed files")
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with code 1 if any warnings are found",
    )
    args = parser.parse_args()

    all_warnings: List[str] = []
    total = 0

    for path in sorted(SEED_DIR.glob("*.yaml")):
        total += 1
        warnings, _ = validate_node(path)
        all_warnings.extend(warnings)

    print(f"Validated {total} seed files.")
    if all_warnings:
        print("Warnings:")
        for warning in all_warnings:
            print(f" - {warning}")
    else:
        print("No warnings.")

    if all_warnings and args.fail_on_warning:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
