#!/usr/bin/env python3
"""
Knowledge Graph Visualization Tool

Generates visual representations of the Spanish learning KG:
- Interactive HTML with pyvis
- Static PNG with pydot/graphviz
- Filtered views by node type, CEFR level, or neighborhood

Enhanced features:
- Edge labels showing relation types in PNG exports
- Color-coded edges by relation type
- Optional CEFR-level hierarchical layout
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Optional

try:
    import networkx as nx
    from pyvis.network import Network
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install networkx pyvis pydot")
    sys.exit(1)

# Edge color scheme by relation type
EDGE_COLORS = {
    "prerequisite_of": "#E74C3C",      # Red - dependency chain
    "realizes": "#3498DB",              # Blue - abstract to concrete
    "contrasts_with": "#E67E22",        # Orange - minimal pairs
    "depends_on": "#9B59B6",            # Purple - structural dependency
    "practice_with": "#2ECC71",         # Green - exercise links
    "addresses_error": "#F39C12",       # Yellow - error correction
}

DEFAULT_EDGE_COLOR = "#95A5A6"  # Gray for unknown types


def load_graph(db_path: str) -> nx.DiGraph:
    """Load KG from SQLite into NetworkX directed graph."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    G = nx.DiGraph()

    # Load nodes with attributes
    cursor.execute("SELECT node_id, type, label, cefr_level FROM nodes")
    for row in cursor:
        G.add_node(
            row["node_id"],
            type=row["type"],
            label=row["label"],
            cefr_level=row["cefr_level"] or "unspecified"
        )

    # Load edges with attributes
    cursor.execute("SELECT source_id, target_id, edge_type FROM edges")
    for row in cursor:
        G.add_edge(
            row["source_id"],
            row["target_id"],
            relation=row["edge_type"]
        )

    conn.close()
    return G


def filter_graph(
    G: nx.DiGraph,
    node_type: Optional[str] = None,
    cefr_level: Optional[str] = None,
    neighborhood: Optional[str] = None,
    depth: int = 1
) -> nx.DiGraph:
    """Filter graph by node type, CEFR level, or neighborhood."""
    if neighborhood:
        # Get ego graph (node + neighbors within depth)
        if neighborhood not in G:
            print(f"Warning: Node '{neighborhood}' not found in graph")
            return nx.DiGraph()
        return nx.ego_graph(G, neighborhood, radius=depth, undirected=False)

    nodes_to_keep = set(G.nodes())

    if node_type:
        nodes_to_keep = {
            n for n in nodes_to_keep
            if G.nodes[n].get("type") == node_type
        }

    if cefr_level:
        nodes_to_keep = {
            n for n in nodes_to_keep
            if G.nodes[n].get("cefr_level") == cefr_level
        }

    return G.subgraph(nodes_to_keep).copy()


def generate_html(G: nx.DiGraph, output_path: str, hierarchical: bool = False):
    """Generate interactive HTML visualization with pyvis."""
    net = Network(
        height="800px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#FFFFFF",
        font_color="#333333"
    )

    # Set layout options (conditional based on hierarchical flag)
    if not hierarchical:
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 200},
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 95
            }
          }
        }
        """)
    else:  # hierarchical layout
        net.set_options("""
        {
          "layout": {
            "hierarchical": {
              "enabled": true,
              "levelSeparation": 150,
              "nodeSpacing": 100,
              "treeSpacing": 200,
              "direction": "UD",
              "sortMethod": "directed"
            }
          },
          "physics": {
            "enabled": false
          }
        }
        """)

    # Add nodes with color by type
    node_colors = {
        "Lexeme": "#3498DB",          # Blue
        "Construction": "#E74C3C",     # Red
        "Morph": "#9B59B6",            # Purple
        "Function": "#2ECC71",         # Green
        "CanDo": "#F39C12",            # Orange
        "Topic": "#1ABC9C",            # Teal
        "Script": "#E67E22",           # Dark Orange
        "PhonologyItem": "#95A5A6",    # Gray
        "DiscourseMove": "#16A085",    # Dark Teal
        "PragmaticCue": "#D35400",     # Dark Red
        "AssessmentCriterion": "#8E44AD", # Dark Purple
    }

    for node in G.nodes():
        node_data = G.nodes[node]
        node_type = node_data.get("type", "Unknown")
        label = node_data.get("label", node)
        cefr = node_data.get("cefr_level", "?")

        color = node_colors.get(node_type, "#95A5A6")
        title = f"{label}\nType: {node_type}\nCEFR: {cefr}"

        net.add_node(
            node,
            label=f"{label}\n[{cefr}]",
            title=title,
            color=color,
            size=25
        )

    # Add edges with color by relation type
    for source, target, data in G.edges(data=True):
        relation = data.get("relation", "unknown")
        color = EDGE_COLORS.get(relation, DEFAULT_EDGE_COLOR)

        net.add_edge(
            source,
            target,
            title=relation,
            color=color,
            arrows="to",
            width=2
        )

    net.save_graph(output_path)
    print(f"✓ Interactive HTML saved to {output_path}")


def generate_png(G: nx.DiGraph, output_path: str, hierarchical_cefr: bool = False):
    """Generate static PNG visualization with pydot/graphviz."""
    try:
        import pydot
    except ImportError:
        print("Error: pydot not installed. Install with: pip install pydot")
        return

    # Position nodes (hierarchical by CEFR if requested)
    if hierarchical_cefr:
        # Group nodes by CEFR level for vertical layering
        cefr_levels = ["A1", "A2", "B1", "B2", "C1", "C2", "unspecified"]
        pos = {}
        for level_idx, level in enumerate(cefr_levels):
            nodes_at_level = [
                n for n in G.nodes()
                if G.nodes[n].get("cefr_level", "unspecified") == level
            ]
            for node_idx, node in enumerate(nodes_at_level):
                pos[node] = (node_idx * 2, -level_idx * 2)  # Spread horizontally, layer vertically
        pos = nx.spring_layout(G, pos=pos, fixed=pos.keys(), k=0.5, iterations=50)
    else:
        pos = nx.spring_layout(G, k=0.5, iterations=50)

    # Create pydot graph
    pydot_graph = pydot.Dot(graph_type="digraph", rankdir="TB", splines="true")

    # Add nodes
    node_colors_dot = {
        "Lexeme": "lightblue",
        "Construction": "lightcoral",
        "Morph": "plum",
        "Function": "lightgreen",
        "CanDo": "orange",
        "Topic": "lightcyan",
        "Script": "peachpuff",
        "PhonologyItem": "lightgray",
        "DiscourseMove": "mediumaquamarine",
        "PragmaticCue": "lightsalmon",
        "AssessmentCriterion": "mediumpurple",
    }

    for node in G.nodes():
        node_data = G.nodes[node]
        node_type = node_data.get("type", "Unknown")
        label = node_data.get("label", node)
        cefr = node_data.get("cefr_level", "?")

        color = node_colors_dot.get(node_type, "lightgray")

        pydot_node = pydot.Node(
            node,
            label=f"{label}\\n[{cefr}]",
            style="filled",
            fillcolor=color,
            fontsize=10
        )
        pydot_graph.add_node(pydot_node)

    # Add edges with labels and colors
    for source, target, data in G.edges(data=True):
        relation = data.get("relation", "unknown")
        color = EDGE_COLORS.get(relation, DEFAULT_EDGE_COLOR)

        pydot_edge = pydot.Edge(
            source,
            target,
            label=relation,
            fontsize=8,
            color=color,
            fontcolor=color
        )
        pydot_graph.add_edge(pydot_edge)

    # Write PNG
    pydot_graph.write_png(output_path)
    print(f"✓ Static PNG saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize Spanish Learning Knowledge Graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate full graph
  python viz_kg.py kg.sqlite

  # Filter by node type
  python viz_kg.py kg.sqlite --type Lexeme

  # Filter by CEFR level
  python viz_kg.py kg.sqlite --cefr A2

  # Show neighborhood around a node
  python viz_kg.py kg.sqlite --neighborhood constr.es.present_indicative --depth 2

  # Generate both HTML and PNG
  python viz_kg.py kg.sqlite --format both

  # Use hierarchical layout
  python viz_kg.py kg.sqlite --hierarchical

  # Use CEFR-based hierarchical layout for PNG
  python viz_kg.py kg.sqlite --format png --hierarchical-cefr
        """
    )

    parser.add_argument(
        "db_path",
        help="Path to kg.sqlite database"
    )
    parser.add_argument(
        "--output",
        default="out/kg_graph",
        help="Output file path (without extension, default: out/kg_graph)"
    )
    parser.add_argument(
        "--format",
        choices=["html", "png", "both"],
        default="html",
        help="Output format (default: html)"
    )
    parser.add_argument(
        "--type",
        help="Filter by node type (e.g., Lexeme, Construction)"
    )
    parser.add_argument(
        "--cefr",
        help="Filter by CEFR level (e.g., A1, A2, B1)"
    )
    parser.add_argument(
        "--neighborhood",
        help="Show neighborhood around specific node ID"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Neighborhood depth (default: 1)"
    )
    parser.add_argument(
        "--hierarchical",
        action="store_true",
        help="Use hierarchical layout in HTML (based on edge direction)"
    )
    parser.add_argument(
        "--hierarchical-cefr",
        action="store_true",
        help="Use CEFR-level hierarchical layout in PNG (A1 top, B1 bottom)"
    )

    args = parser.parse_args()

    # Validate database path
    if not Path(args.db_path).exists():
        print(f"Error: Database not found at {args.db_path}")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load and filter graph
    print(f"Loading graph from {args.db_path}...")
    G = load_graph(args.db_path)
    print(f"Loaded {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    if args.type or args.cefr or args.neighborhood:
        print(f"Applying filters...")
        G = filter_graph(
            G,
            node_type=args.type,
            cefr_level=args.cefr,
            neighborhood=args.neighborhood,
            depth=args.depth
        )
        print(f"Filtered to {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    if G.number_of_nodes() == 0:
        print("Warning: No nodes in filtered graph. Check filter parameters.")
        sys.exit(1)

    # Generate visualizations
    if args.format in ["html", "both"]:
        html_path = f"{args.output}.html"
        generate_html(G, html_path, hierarchical=args.hierarchical)

    if args.format in ["png", "both"]:
        png_path = f"{args.output}.png"
        generate_png(G, png_path, hierarchical_cefr=args.hierarchical_cefr)

    print("\n✓ Visualization complete!")


if __name__ == "__main__":
    main()
