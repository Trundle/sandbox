#!/usr/bin/env python3
import sys
from optparse import OptionParser

# Python 3
from urllib.parse import urljoin
from xmlrpc.client import ServerProxy, Error as XMLRPCError


URL = 'http://bpaste.net/'


def pastebin(source, syntax, parent='', filename='', mimetype='', private=False):
    """Upload to a pastebin and output the URL"""
    pasteservice = ServerProxy(urljoin(URL, 'xmlrpc/'))
    paste_id = pasteservice.pastes.newPaste(syntax, source, parent,
                                            filename, mimetype, private)
    return urljoin(URL, '/show/%s/' % (paste_id, ))


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = OptionParser()
    parser.add_option('-p', dest='parent', type='string', default='')
    parser.add_option("-s", dest="syntax", type='string', default='pycon',
                  help="Syntax highlighting: py, bash, sql, xml, c, c++, etc")
    parser.add_option('-P', dest='private', action='store_false', default=True,
                      help="Create a public paste")
    options, args = parser.parse_args(args)
    if args:
        parser.print_usage()
        return 1

    source = sys.stdin.read()
    try:
        url = pastebin(source, options.syntax, options.parent,
                       private=options.private)
    except XMLRPCError:
        exc = sys.exc_info()[1]
        sys.stderr.write('Paste failed: %s\n' % (str(exc), ))
    else:
        sys.stdout.write('Paste succeeded, available as %s\n' % (url, ))

    return 0



if __name__ == '__main__':
    sys.exit(main())
