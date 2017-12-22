import json
import sys
import logging

import spotipy
import spotipy.util as util


logger = logging.getLogger('mover')
ENTITIES = {
    'track': {
        'get': 'current_user_saved_tracks',
        'set': 'current_user_saved_tracks_add',
        'key': 'track',
    },
    'album': {
        'get': 'current_user_saved_albums',
        'set': 'current_user_saved_albums_add',
        'key': 'album',
    },
    'artist': {
        'get': 'current_user_followed_artists',
        'set': 'user_follow_artists',
        'key': None,
    },
}
SCOPE = (
    'user-library-read '
    'user-library-modify '
    'user-follow-modify '
    'user-follow-read'
)


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    spotify = connect()
    # dump_library(spotify)
    load_library(spotify)


def dump_library(spotify):
    for entity, methods in ENTITIES.items():
        method = getattr(spotify, methods['get'])
        items = full(spotify, result_root(method()))
        with open(entity + '.json', 'wt') as fp:
            json.dump(items, fp, indent=2)


def load_library(spotify):
    for entity, methods in ENTITIES.items():
        method = getattr(spotify, methods['set'])
        with open(entity + '.json', 'rt') as fp:
            items = json.load(fp)
        ids = item_ids(methods['key'], items)
        for chunk in chunks(ids, 20):
            method(chunk)


def chunks(items, size):
    chunk = []
    for item in items:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def item_ids(key, items):
    if key:
        return reversed([
            item[key]['id']
            for item in items
        ])
    else:
        return reversed([
            item['id']
            for item in items
        ])


def authenticate():
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        raise RuntimeError("Usage: %s username" % sys.argv[0])
    token = util.prompt_for_user_token(username, SCOPE)
    if token:
        return token
    else:
        raise RuntimeError("Can't get token for %s" % username)


def full(spotify, result):
    items = result['items']
    next_url = result['next']
    while next_url:
        result = result_root(spotify.next(result))
        items.extend(result['items'])
        next_url = result['next']
    return items


def result_root(result):
    if 'items' in result:
        return result
    else:
        return next(iter(result.values()))


def connect():
    return spotipy.Spotify(auth=authenticate())


if __name__ == '__main__':
    main()
