#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    pysss
    ~~~~~
    A simple streaming server which streams stdout and stderr of spawned
    processes, written in pure Python.

    :copyright: Copyright 2009 by Andreas Stührk.
    :license: Modified BSD.
"""

import asyncore
import subprocess
import sys
from optparse import OptionParser
from socket import AF_INET, SOCK_STREAM, error as socket_error


class Connection(object, asyncore.dispatcher):
    def __init__(self, sock, map_, exec_args, verbose):
        asyncore.dispatcher.__init__(self, sock, map=map_)
        self.process = subprocess.Popen(exec_args, close_fds=True,
                                        stdout=self.fileno(),
                                        stderr=self.fileno())
        self.verbose = verbose

    @property
    def alive(self):
        """
        Return whether the spawned process is alive or not.
        """
        return self.process.poll() is None

    def readable(self):
        if not self.alive:
            if self.verbose:
                print 'Closing connection to %s:%i' % self.getpeername()
            self.close()
        return False

    def writable(self):
        return False


class Listener(asyncore.dispatcher):
    def __init__(self, addr, map_, exec_args, max_connections, verbose):
        asyncore.dispatcher.__init__(self, map=map_)
        self.create_socket(AF_INET, SOCK_STREAM)
        self.bind(addr)
        self.listen(5)
        self.exec_args = exec_args
        self.max_connections = max_connections
        self.verbose = verbose

    def handle_accept(self):
        """
        This is called when a client connected.
        """
        sock, addr = self.accept()
        if not self.slot_available():
            sock.setblocking(False)
            try:
                sock.send('Sorry, no slot available. Try again later.\n')
            except socket_error:
                pass
            if self.verbose:
                print 'No slot available, dropping connection to %s:%i' % addr
        else:
            if self.verbose:
                print 'Client connected: %s:%i' % addr
            Connection(sock, self._map, self.exec_args, self.verbose)

    def slot_available(self):
        """
        Return whether a free slot is availalble or not.
        """
        if not self.max_connections:
            return True
        else:
            connections = filter(lambda obj: hasattr(obj, 'process') and
                                             obj.alive,
                                 self._map.itervalues())
            return len(connections) < self.max_connections


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    # Option parsing
    parser = OptionParser(usage='Usage: %prog [options] <port> [<port> ...] '
                                '-- <exec file> [arguments]')
    parser.add_option('--host', default='')
    parser.add_option('-m', '--max-connections', type='int', default=0)
    parser.add_option('-v', '--verbose', action='store_true')

    try:
        split_index = args.index('--')
    except ValueError:
        parser.print_usage()
        return 1

    args, exec_args = args[:split_index], args[split_index + 1:]
    if not exec_args:
        parser.print_usage()
        return 1

    try:
        options, args = parser.parse_args(args)
        args = map(int, args)
        if not args:
            raise ValueError()
    except ValueError:
        parser.print_usage()
        return 1
    except SystemExit:
        return 1
    # Yay, option parsing finished

    connection_pool = dict()
    for port in args:
        Listener((options.host, port), connection_pool, exec_args,
                 options.max_connections, options.verbose)

    asyncore.loop(map=connection_pool)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
