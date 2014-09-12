#!/usr/bin/env python3

import sys
import requests
import requests.exceptions
from argparse import ArgumentParser
from urllib.parse import urljoin

URL = 'https://bpaste.net'
DURATIONS = ('1day', '1week', '1month', 'never')
DEFAULT_DURATION = DURATIONS[0]

def pastebin(source, syntax, expiry=DEFAULT_DURATION):
    """Upload to a pastebin and output the URL"""

    if expiry not in DURATIONS:
        raise ValueError("{0} is not a valid expiry duration".format(expiry))

    url = urljoin(URL, '/json')
    payload = {
        'code': source,
        'lexer': syntax,
        'expiry': expiry
    }

    response = requests.post(url, data=payload, verify=True)
    response.raise_for_status()

    data = response.json()

    return (urljoin(URL, '/show/{0}'.format(data['paste_id'])),
            urljoin(URL, '/remove/{0}'.format(data['removal_id'])))

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = ArgumentParser(description='Post pastes to {0}.'.format(URL))
    parser.add_argument('-s', dest='syntax', default='pycon',
                        help='Syntax highlighting: py, bash, sql, xml, c, c++, etc')
    parser.add_argument('-e', dest='expiry', choices=DURATIONS,
                        default=DEFAULT_DURATION,
                        help='Expiry time of the paste')
    args = parser.parse_args(args)
    if not args:
        parser.print_usage()
        return 1

    source = sys.stdin.read()
    try:
        url, delete_url = pastebin(source, args.syntax, args.expiry)
    except requests.exceptions.RequestException as exc:
        print('Paste failed: {0}'.format(exc), file=sys.stderr)
    else:
        print("Paste succedded, available as {0}.".format(url))
        print("It can be removed by opening {0}.".format(delete_url))

    return 0

if __name__ == '__main__':
    sys.exit(main())
