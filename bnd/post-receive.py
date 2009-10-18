#!/usr/bin/python

"""
    Post-commit hook for git.
"""

from __future__ import with_statement
import os
import subprocess
import sys
from xmlrpclib import ServerProxy


XMLRPC_ADDR =  ('localhost', 7009)
CHANNEL = '#t'


def get_output(*args):
    data = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    return data.strip()

def send_commit_message(bot, repo, refname, rev):
    message = get_output('git', 'cat-file', 'commit', rev)

    attributes = dict(branch=refname, repo=repo, rev=rev[:12])
    linesiter = iter(message.splitlines())
    for line in linesiter:
        if not line:
            break
        key, value = line.split(None, 1)
        if key in ['author', 'committer']:
            # Remove date
            value = value.rsplit(None, 2)[0]
            # Remove mail address
            try:
                value = value[:value.index(' <')]
            except ValueError:
                pass
        attributes[key] = value
    attributes['message'] = ' '.join(filter(bool, linesiter))

    bot.say(CHANNEL,
            ('%(author)s committed rev %(rev)s to '
              '%(repo)s/%(branch)s: %(message)s') % attributes)


def main():
    bot = ServerProxy('http://%s:%i' % XMLRPC_ADDR)
    repo = os.path.basename(os.getcwd())
    if repo.endswith('.git'):
        repo = repo[:-len('.git')]

    for line in sys.stdin:
        old, new, refname = line.split()
        if new.strip('0') and refname.startswith('refs/heads/'):
            refname = refname[len('refs/heads/'):]
            revisions = get_output('git', 'rev-list',
                                    '%s..%s' % (old, new)).splitlines()
            for revision in reversed(revisions):
                send_commit_message(bot, repo, refname, revision)

if __name__ == '__main__':
    main()
