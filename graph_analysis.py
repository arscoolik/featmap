"""Analyze an artist collaboration snapshot without API access."""
import argparse
import json
from collections import Counter
from pathlib import Path

import networkx as nx

from graph_data import build_graph, load_data


def ranking(values, limit):
    return [{"artist": name, "score": value} for name, value in
            sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def analyze_graph(graph, top=10, samples=100, exact_paths=False):
    """Compute topology and rankings; sample expensive metrics on large graphs."""
    if top < 1 or samples < 1:
        raise ValueError("top and samples must be positive")
    n = len(graph)
    components = sorted(nx.connected_components(graph), key=lambda c: (-len(c), sorted(c)))
    largest = graph.subgraph(components[0]).copy() if components else nx.Graph()
    k = min(samples, n)
    betweenness = nx.betweenness_centrality(graph, k=k, seed=42) if n else {}
    communities = list(nx.community.louvain_communities(graph, seed=42)) if graph.number_of_edges() else [{v} for v in graph]
    communities.sort(key=lambda c: (-len(c), sorted(c)))
    # Stream distances: never retain all pairs or all paths in memory.
    import random
    sources = sorted(largest)
    exact = exact_paths or len(sources) <= samples
    if not exact:
        sources = random.Random(42).sample(sources, samples)
    distance_sum = pair_count = diameter = 0
    endpoints = None
    for source in sources:
        lengths = nx.single_source_shortest_path_length(largest, source)
        distance_sum += sum(lengths.values())
        pair_count += len(lengths) - 1
        for target, distance in lengths.items():
            if distance > diameter:
                diameter, endpoints = distance, (source, target)
    return {
        "artists": n, "collaborations": graph.number_of_edges(),
        "density": nx.density(graph),
        "average_degree": sum(dict(graph.degree()).values()) / n if n else 0,
        "degree_distribution": dict(sorted(Counter(dict(graph.degree()).values()).items())),
        "connected_components": len(components), "component_sizes": [len(c) for c in components],
        "largest_component_fraction": len(largest) / n if n else 0,
        "isolated_artists": sorted(nx.isolates(graph)),
        "average_clustering": nx.average_clustering(graph) if n else 0,
        "transitivity": nx.transitivity(graph),
        "triangles": sum(nx.triangles(graph).values()) // 3,
        "top_collaborators": ranking(dict(graph.degree()), top),
        "top_betweenness": ranking(betweenness, top),
        "betweenness_sources": k,
        "articulation_points": sorted(nx.articulation_points(graph)),
        "bridges": sorted(sorted(edge) for edge in nx.bridges(graph)),
        "communities": [sorted(c) for c in communities],
        "modularity": nx.community.modularity(graph, communities) if graph.number_of_edges() else 0,
        "largest_component_paths": {
            "exact": exact, "sources": len(sources),
            "diameter" if exact else "diameter_lower_bound": diameter if sources else None,
            "average_shortest_path_length" if exact else "sampled_average_shortest_path_length": distance_sum / pair_count if pair_count else None,
            "example_path": nx.shortest_path(largest, *endpoints) if endpoints else [],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="artist_tracks_yandex.json")
    parser.add_argument("--threshold", type=int, default=1000, help="exclusive rank cutoff; 0 includes all ranks")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--exact-paths", action="store_true", help="compute all-pairs distances in the largest component")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.top < 1 or args.samples < 1:
        parser.error("--top and --samples must be positive")
    data = load_data(args.input)
    result = analyze_graph(build_graph(data, args.threshold or None), args.top, args.samples, args.exact_paths)
    result["snapshot_artists"] = len(data)
    result["excluded_by_rank"] = len(data) - result["artists"]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{result['artists']} artists · {result['collaborations']} collaborations · {result['connected_components']} components")
    print(f"Clustering: {result['average_clustering']:.3f} · Communities: {len(result['communities'])} · Bridges: {len(result['bridges'])}")
    print("Most collaborators:")
    for entry in result["top_collaborators"]:
        print(f"  {entry['artist']}: {entry['score']}")
    print("Largest component paths:", json.dumps(result["largest_component_paths"], ensure_ascii=False))
    if args.output:
        print(f"Full report: {args.output}")


if __name__ == "__main__":
    main()
