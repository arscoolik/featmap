"""Export an interactive Plotly collaboration graph."""
import argparse
from html import escape
from pathlib import Path

import networkx as nx

from graph_data import build_graph, load_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', default='artist_tracks_yandex.json')
    parser.add_argument('--threshold', type=int, default=1000)
    parser.add_argument('--output', type=Path, default=Path('output/artist_graph.html'))
    args = parser.parse_args()
    import plotly.graph_objects as go
    graph = build_graph(load_data(args.input), args.threshold or None)
    positions = nx.spring_layout(graph, seed=42)
    x, y = [], []
    for a, b in graph.edges:
        x.extend([positions[a][0], positions[b][0], None])
        y.extend([positions[a][1], positions[b][1], None])
    edges = go.Scatter(x=x, y=y, mode='lines', line={'width': 0.5, 'color': '#888'}, hoverinfo='skip')
    nodes = list(graph)
    markers = go.Scatter(
        x=[positions[n][0] for n in nodes], y=[positions[n][1] for n in nodes],
        mode='markers', text=[f'{escape(n)} · {graph.degree(n)} collaborators' for n in nodes],
        hoverinfo='text', marker={'size': 9, 'color': [graph.degree(n) for n in nodes],
                                  'showscale': True, 'colorbar': {'title': 'Connections'}})
    figure = go.Figure([edges, markers])
    figure.update_layout(title='Artist collaborations', showlegend=False, template='plotly_dark',
                         xaxis={'visible': False}, yaxis={'visible': False}, height=850)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(args.output, include_plotlyjs=True)
    print(f'Visualization: {args.output}')


if __name__ == '__main__':
    main()
