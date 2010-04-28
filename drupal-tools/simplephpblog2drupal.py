#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    A small converter for importing simplephpblog blog entries into drupal
    using the XML-RPC-Blog-API.

    :copyright: Copyright (C) 2009 by Andeas Stührk.
                Partial copyright by Fredrik Lundh.
    :license: Modified BSD.
"""

from __future__ import with_statement

import htmlentitydefs
import os.path
import re
import sys
from contextlib import closing
from datetime import datetime
from glob import glob
from gzip import GzipFile
from itertools import izip
from xmlrpclib import ServerProxy


def unescape(text):
    """
    Removes HTML entities from a text string.

    Written by Fredrik Lundh.
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def read_entry(filename):
    with closing(GzipFile(filename, 'r')) as entry_file:
        data = entry_file.read().decode('latin-1').split('|')
    entry = dict(izip(*[iter(data)] * 2))
    entry['CONTENT'] = unescape(entry['CONTENT'])
    entry['DATE'] = datetime.fromtimestamp(int(entry['DATE']))
    return entry


def post_entry(server, username, password, entry):
    server.metaWeblog.newPost(
        'blog',
        username,
        password,
        dict(
            title=entry['SUBJECT'],
            description=entry['CONTENT'],
        ),
        False
    )


def main(args=sys.argv[1:]):
    server = ServerProxy(args[0])
    entry_files = glob(os.path.join(args[3], '*', '*', 'entry*.txt.gz'))
    for filename in entry_files:
        entry = read_entry(filename)
        post_entry(server, args[1], args[2], entry)


if __name__ == '__main__':
    main()
