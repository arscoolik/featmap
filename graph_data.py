"""Shared loading and graph construction for collaboration snapshots."""
import json
from pathlib import Path

import networkx as nx


def load_data(path):
    """Read wrapped Yandex, plain Yandex, or legacy Spotify snapshots."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data.get("data"), dict):
        data = data["data"]
    normalized = {}
    for name, record in data.items():
        if isinstance(record, list):
            normalized[name] = {"info": [None], "feats": record}
        else:
            normalized[name] = record
    return normalized


def build_graph(data, threshold=1000):
    """Use known artists only; include ranks strictly below the cutoff.

    A missing rank is included. Edges are unweighted, undirected observations,
    not counts of shared tracks. Self collaborations are ignored.
    """
    graph = nx.Graph()
    for name, record in data.items():
        info = record.get("info") or [None]
        rank = info[0]
        if threshold is None or rank is None or rank < threshold:
            graph.add_node(name, rank=rank)
    for name in list(graph):
        for collaborator in data[name].get("feats", []):
            if collaborator in graph and collaborator != name:
                graph.add_edge(name, collaborator)
    return graph
