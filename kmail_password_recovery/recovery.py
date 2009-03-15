#!/usr/bin/env python

import os.path
import sys


def decrypt(data):
    """Python equivalent of kmail's KMAccount::encryptStr"""
    result = list()
    for char in data:
        if ord(char) <= 0x21:
            result.append(char)
        else:
            result.append(unichr(0x1001F - ord(char)))
    return ''.join(result)


def main():
    if len(sys.argv) != 2:
        exec_file = os.path.basename(sys.argv[0])
        print >> sys.stderr, 'Usage: %s <encrypted password>' % exec_file
        return 1

    pwd = sys.argv[1].decode('utf-8')
    print decrypt(pwd).encode(sys.stdout.encoding)

    return 0


if __name__ == '__main__':
    sys.exit(main())
