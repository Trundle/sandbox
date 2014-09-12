#!/usr/bin/env python3

import sys
import requests
import requests.exceptions
from argparse import ArgumentParser
from urllib.parse import urljoin

# service URL
URL = 'https://bpaste.net'

# expiry duration values
DURATIONS = ('1day', '1week', '1month', 'never')
DEFAULT_DURATION = DURATIONS[0]

# actions
ACTIONS = ('paste', 'remove', 'show')

def paste(source, syntax, expiry=DEFAULT_DURATION):
    """Upload to a pastebin and output the URL"""

    if expiry not in DURATIONS:
        raise ValueError("{0} is not a valid expiry duration".format(expiry))

    url = urljoin(URL, '/json/new')
    payload = {
        'code': source,
        'lexer': syntax is not None or 'text',
        'expiry': expiry
    }

    response = requests.post(url, data=payload, verify=True)
    response.raise_for_status()

    data = response.json()

    return (urljoin(URL, '/show/{0}'.format(data['paste_id'])),
            urljoin(URL, '/remove/{0}'.format(data['removal_id'])))

def remove_paste(removal_id):
    """Remove paste"""

    url = urljoin(URL, '/json/remove')
    payload = {
        'removal_id': removal_id
    }

    response = requests.post(url, data=playload, verify=True)
    if response.status_code not in (requests.codes.ok,
                                    requests.codes.not_founds):
        response.raise_for_status()

    return response.status_code == requests.codes.ok

def fetch_paste(paste_id):
    """Fetch paste"""

    url = urljoin(URL, '/json/show/{0}'.format(paste_id))

    response = requests.get(url, verify=True)
    response.raise_for_status()

    data = response.json()

    return data['raw']


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = ArgumentParser(description='Manage pastes at {0}.'.format(URL))
    parser.add_argument('action', default='paste', nargs='?', choices=ACTIONS,
                        help='Action to perform')
    parser.add_argument('-s', '--syntax', dest='syntax', default='pycon',
                        help='Syntax highlighting: py, bash, sql, xml, c, c++, etc')
    parser.add_argument('-e', '--expiry', dest='expiry', choices=DURATIONS,
                        default=DEFAULT_DURATION,
                        help='Expiry time of the paste')
    parser.add_argument('-i', '--id', dest='pasteid',
                        help='Paste/Removal ID used for show and remove.')

    args = parser.parse_args(args)
    if not args:
        parser.print_usage()
        return 1

    try:
        if args.action == 'paste':
            source = sys.stdin.read()
            url, delete_url = paste(source, args.syntax, args.expiry)
            print('Paste succedded, available as {0}.'.format(url))
            print('It can be removed by opening {0}.'.format(delete_url))
        elif args.action == 'remove':
            if remove_paste(args.pasteid):
                print('Successfully removed paste {0}.'.format(args.pasteid))
            else:
                print('Failed to remove paste with removal id {0}: no such paste.'.format(args.pasteid),
                      file=sys.stderr)
                return 1
        elif args.action == 'show':
            print(fetch_paste(args.pasteid))
    except requests.exceptions.RequestException as exc:
        print('Action "{0}" failed: {1}'.format(args.action, exc),
              file=sys.stderr)
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
