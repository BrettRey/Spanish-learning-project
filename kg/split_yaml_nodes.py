#!/usr/bin/env python3
"""
Split multi-node YAML files into individual node files.

The KG build system expects one node per YAML file, but it's easier to author
nodes in batches. This script splits multi-node files into individual files.

Usage:
    python kg/split_yaml_nodes.py kg/seed/b1_cando_nodes.yaml
"""

import argparse
import sys
from pathlib import Path

import yaml


def split_yaml_file(input_file: Path, output_dir: Path = None) -> int:
    """
    Split a multi-node YAML file into individual node files.

    Args:
        input_file: Path to multi-node YAML file
        output_dir: Directory to write individual node files (default: same as input)

    Returns:
        Number of nodes processed
    """
    if output_dir is None:
        output_dir = input_file.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the multi-node file
    with open(input_file) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dictionary at top level of {input_file}")

    # Extract nodes and edges (if present)
    nodes = data.get("nodes", [])
    global_edges = data.get("prerequisites", [])

    if not nodes:
        print(f"Warning: No nodes found in {input_file}", file=sys.stderr)
        return 0

    nodes_written = 0

    # Process each node
    for node in nodes:
        if not isinstance(node, dict):
            print(f"Warning: Skipping non-dict node: {node}", file=sys.stderr)
            continue

        node_id = node.get("node_id")
        if not node_id:
            print(f"Warning: Node missing node_id: {node}", file=sys.stderr)
            continue

        # Convert to build script format
        output_node = {
            "id": node_id,
            "type": node.get("type"),
            "label": node.get("label"),
            "cefr_level": node.get("cefr_level"),
            "source": node.get("source"),
        }

        # Add diagnostics if present
        if "diagnostics" in node:
            diagnostics = node["diagnostics"]
            if isinstance(diagnostics, list):
                output_node["diagnostics"] = diagnostics
            elif isinstance(diagnostics, dict):
                # Convert dict diagnostics to list of strings
                diag_list = []
                for key, value in diagnostics.items():
                    if isinstance(value, str):
                        diag_list.append(f"{key}: {value}")
                    else:
                        diag_list.append(f"{key}: {str(value)}")
                output_node["diagnostics"] = diag_list

        # Add prompts if present
        if "prompts" in node:
            output_node["prompts"] = node["prompts"]

        # Add examples if present
        if "examples" in node:
            output_node["examples"] = node["examples"]

        # Add corpus_examples if present
        if "corpus_examples" in node:
            output_node["corpus_examples"] = node["corpus_examples"]

        # Add strand if present
        if "strand" in node:
            output_node["strand"] = node["strand"]

        # Add frequency info if present
        for field in ["frequency", "frequency_source", "frequency_bands"]:
            if field in node:
                output_node[field] = node[field]

        # Find edges that reference this node
        node_prerequisites = []
        for edge in global_edges:
            if edge.get("target_id") == node_id:
                # This is a prerequisite for this node
                node_prerequisites.append(edge.get("source_id"))

        if node_prerequisites:
            output_node["prerequisites"] = node_prerequisites

        # Write individual node file
        output_file = output_dir / f"{node_id}.yaml"
        with open(output_file, "w") as f:
            yaml.dump(output_node, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        nodes_written += 1
        print(f"  Created: {output_file.name}")

    return nodes_written


def main():
    parser = argparse.ArgumentParser(description="Split multi-node YAML files")
    parser.add_argument(
        "input_files",
        nargs="+",
        type=Path,
        help="Multi-node YAML files to split",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: same as input file)",
    )

    args = parser.parse_args()

    total_nodes = 0
    for input_file in args.input_files:
        if not input_file.exists():
            print(f"Error: File not found: {input_file}", file=sys.stderr)
            continue

        print(f"\nProcessing: {input_file.name}")
        print(f"{'─'*60}")

        try:
            count = split_yaml_file(input_file, args.output_dir)
            total_nodes += count
            print(f"\n✅ Processed {count} nodes from {input_file.name}")
        except Exception as e:
            print(f"❌ Error processing {input_file}: {e}", file=sys.stderr)

    print(f"\n{'='*60}")
    print(f"Total nodes created: {total_nodes}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
