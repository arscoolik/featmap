import json
import tempfile
import unittest
from pathlib import Path

import networkx as nx

from crawler import crawl
from graph_analysis import analyze_graph
from graph_data import build_graph, load_data


class AnalysisTests(unittest.TestCase):
    def test_path_and_isolate(self):
        graph = nx.Graph([('a', 'b'), ('b', 'c')])
        graph.add_node('alone')
        result = analyze_graph(graph)
        self.assertEqual(result['component_sizes'], [3, 1])
        self.assertEqual(result['largest_component_paths']['diameter'], 2)
        self.assertAlmostEqual(result['largest_component_paths']['average_shortest_path_length'], 4 / 3)
        self.assertEqual(result['articulation_points'], ['b'])
        self.assertEqual(len(result['bridges']), 2)
        self.assertEqual(result['top_collaborators'][0]['artist'], 'b')

    def test_triangle_and_empty(self):
        result = analyze_graph(nx.complete_graph(['a', 'b', 'c']))
        self.assertEqual(result['triangles'], 1)
        self.assertEqual(result['average_clustering'], 1)
        self.assertEqual(result['bridges'], [])
        empty = analyze_graph(nx.Graph())
        self.assertEqual(empty['artists'], 0)
        self.assertIsNone(empty['largest_component_paths']['diameter'])

    def test_filter_and_formats(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'data.json'
            for wrapped in (False, True):
                data = {'a': {'info': [999], 'feats': ['a', 'b', 'c', 'unknown']},
                        'b': {'info': [1000], 'feats': []}, 'c': {'info': [1], 'feats': []}}
                path.write_text(json.dumps({'data': data} if wrapped else data))
                graph = build_graph(load_data(path))
                self.assertEqual(set(graph), {'a', 'c'})
                self.assertEqual(list(graph.edges), [('a', 'c')])
            path.write_text(json.dumps({'a': ['b'], 'b': []}))
            self.assertEqual(build_graph(load_data(path)).number_of_edges(), 1)

    def test_sampling_is_explicit(self):
        result = analyze_graph(nx.path_graph([str(i) for i in range(20)]), samples=2)
        self.assertFalse(result['largest_component_paths']['exact'])
        self.assertIn('diameter_lower_bound', result['largest_component_paths'])

    def test_resume_preserves_data_and_edges(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'data.json'
            path.write_text(json.dumps({'a': {'info': [1], 'feats': ['b']}}))
            crawl(path, [], lambda name: {'info': [2], 'feats': ['a', 'c']}, limit=1)
            data = load_data(path)
            self.assertIn('a', data)
            self.assertEqual(data['b']['feats'], ['a', 'c'])


if __name__ == '__main__':
    unittest.main()
