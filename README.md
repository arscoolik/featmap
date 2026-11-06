# Featmap

Explore music scenes through artist collaborations. Featmap collects artist credits from Yandex Music or Spotify, builds an undirected network, exports an interactive HTML map, and produces a JSON analysis report.

The included historical snapshots let you explore the project **without API keys**. The larger snapshot contains 6,131 artist records; the smaller Spotify snapshot contains 10 collected artists.

## Quick start

Requires Python 3.10 or newer. From the project directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python graph_analysis.py --output output/analysis.json
python graph.py --output output/artist_graph.html
```

Open `output/artist_graph.html` in a browser. The HTML embeds Plotly and works offline. Hover over a node for its artist name and number of collaborators. Generated files go in the ignored `output/` directory. If an old `.venv` points to a missing Python installation, create a fresh environment in another directory and activate it.

## Analysis

```sh
# Include every recorded artist, regardless of rank
python graph_analysis.py --threshold 0 --output output/all-artists.json

# Exact distances across the largest component (can take longer)
python graph_analysis.py --exact-paths --top 20 --output output/exact.json

# Analyze the smaller Spotify snapshot
python graph_analysis.py artist_tracks.json --output output/spotify.json
```

The full JSON report includes:

- Artist/edge counts, density, average degree, and degree distribution.
- Connected component sizes and isolated artists.
- Top artists by collaborator count and betweenness centrality (artists connecting different parts of the network).
- Average clustering, transitivity, and triangle count.
- Louvain communities and modularity.
- Bridges and articulation points: connections or artists whose removal disconnects part of the graph.
- Diameter, a representative shortest path, and average shortest-path length **within the largest component**.

By default, ranks must be strictly below 1,000; lower Yandex monthly rank values represent higher placement. Missing ranks are included, as in the legacy Spotify snapshot. Both analysis and rendering use the same filter and retain isolated nodes. Only artists with their own records become nodes; references to uncollected artists are excluded.

For components larger than `--samples` (default 100), path metrics use a deterministic sample of source artists. The report explicitly labels the diameter as a lower bound and the average as sampled. `--exact-paths` makes path metrics exact; it does not change betweenness sampling. Betweenness uses up to `--samples` source nodes with a fixed seed. All distances count edges, not popularity or collaboration frequency. Diameter means the longest **shortest** path, not the longest simple path.

### Included snapshot: example findings

At the default rank cutoff, the historical Yandex snapshot has 941 artists and 1,481 edges across 239 connected components. Its largest component contains 592 artists (62.9%); exact diameter is 16 hops and average shortest-path length is 5.443. There are 209 bridges, and average clustering is 0.133. Harddope has the most observed collaborators (27), followed by DFM, Yanix, and Баста (20 each). These results describe the filtered, incomplete snapshot, not the full providers' catalogs.

## Collecting fresh data (optional)

Credentials are read from environment variables. `.env.example` lists the names, but scripts do not automatically load `.env` files. Never commit credentials or authentication caches.

```sh
export YANDEX_TOKEN='your-token'
python loader_yandex.py --seed ATL --seed Yanix --limit 100 --output output/yandex.json

export SPOTIPY_CLIENT_ID='your-client-id'
export SPOTIPY_CLIENT_SECRET='your-client-secret'
python loader.py --seed Drake --limit 100 --output output/spotify.json
```

Yandex collection defaults to a maximum monthly rank of 10,000; Spotify defaults to at least 100,000 followers (`--min-followers`). Use `--verbose` for collection progress. `--limit` bounds newly collected artist records per run. Collection can still make many API requests per artist; provider access restrictions and rate limits apply.

The collectors search by name and use the first result, then traverse album credits. They paginate albums (and Spotify tracks), save after each completed artist, and preserve existing records on resume. Rerun with the same output path to continue discovering uncollected collaborators. Existing artists are not refreshed. API failures stop collection after saving completed records; rerunning retries unfinished work. No credentials are needed for `--help`.

## Data limitations

These are historical, incomplete snapshots, not an authoritative map of a genre. The original Yandex collector discarded links to already visited artists, so some collaborations cannot be recovered without recollecting into a new file. Artist-name ambiguity, provider coverage, rank filtering, and crawl seeds all affect results. An edge means at least one observed shared credit; the files do not retain track IDs or collaboration counts. Communities describe this snapshot and should not be treated as genre labels or causal findings.

`graph2.py` remains a compatibility alias for `graph.py`; the duplicate PyVis renderer was consolidated into the Plotly exporter.


