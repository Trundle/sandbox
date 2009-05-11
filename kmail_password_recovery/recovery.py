#!/usr/bin/env python

import os.path
import sys
from ConfigParser import ConfigParser, NoOptionError


def decrypt(data):
    """Python equivalent of kmail's KMAccount::encryptStr"""
    result = list()
    for char in data:
        if ord(char) <= 0x21:
            result.append(char)
        else:
            result.append(unichr(0x1001F - ord(char)))
    return ''.join(result)


def main(args=sys.argv[1:]):
    if len(sys.argv) != 2:
        exec_file = os.path.basename(sys.argv[0])
        print >> sys.stderr, 'Usage: %s <config file>' % exec_file
        return 1

    config = ConfigParser()
    config.read(args[0])
    for section in config.sections():
        if not section.startswith('Transport '):
            continue
        name = config.get(section, 'name')
        try:
            pwd = decrypt(config.get(section, 'pass').decode('utf-8'))
        except NoOptionError:
            pwd = str()
        print '%s:%s' % (name, pwd)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
