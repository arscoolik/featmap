"""Collect Yandex Music collaborations using YANDEX_TOKEN."""
import argparse
import logging
import os
import time

from crawler import crawl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='artist_tracks_yandex.json')
    parser.add_argument('--seed', action='append', default=[])
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--max-rank', type=int, default=10000)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    token = os.environ.get('YANDEX_TOKEN')
    if not token:
        parser.error('Set YANDEX_TOKEN')
    from yandex_music import Client
    client = Client(token).init()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    def fetch(name):
        result = client.search(name, type_='artist')
        artists = result.artists.results if result.artists else []
        if not artists:
            return None
        artist = artists[0]
        rank = artist.ratings.month if artist.ratings else None
        if rank is None or rank > args.max_rank:
            return None
        collaborators = set()
        page = 0
        while True:
            albums = client.artists_direct_albums(artist.id, page=page, page_size=100).albums
            if not albums:
                break
            for album in albums:
                for volume in client.albums_with_tracks(album.id).volumes:
                    for track in volume:
                        collaborators.update(a.name for a in track.artists if str(a.id) != str(artist.id))
                time.sleep(0.1)
            if len(albums) < 100:
                break
            page += 1
        return {'info': [rank], 'feats': sorted(collaborators)}

    crawl(args.output, args.seed or ['ATL', 'Yanix'], fetch, args.limit)


if __name__ == '__main__':
    main()
