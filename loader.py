"""Collect Spotify collaborations using client credentials from the environment."""
import argparse
import logging
import os

from crawler import crawl


def pages(client, page):
    while page:
        yield from page['items']
        page = client.next(page) if page.get('next') else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='artist_tracks.json')
    parser.add_argument('--seed', action='append', default=[])
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--min-followers', type=int, default=100000)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    if not all(os.environ.get(k) for k in ('SPOTIPY_CLIENT_ID', 'SPOTIPY_CLIENT_SECRET')):
        parser.error('Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET')
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    client = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    def fetch(name):
        artists = client.search(q=f'artist:{name}', type='artist', limit=1)['artists']['items']
        if not artists or artists[0]['followers']['total'] < args.min_followers:
            return None
        artist = artists[0]
        collaborators = set()
        albums = pages(client, client.artist_albums(artist['id'], album_type='album,single', limit=50))
        for album_id in dict.fromkeys(a['id'] for a in albums):
            for track in pages(client, client.album_tracks(album_id, limit=50)):
                collaborators.update(a['name'] for a in track['artists'] if a['id'] != artist['id'])
        return {'info': [None], 'feats': sorted(collaborators)}

    crawl(args.output, args.seed or ['Drake'], fetch, args.limit)


if __name__ == '__main__':
    main()
