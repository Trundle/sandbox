# -*- coding: utf-8 -*-
# Copyright (C) 2011-2012, Sebastian Ramacher
# This file is released under a modified BSD license. See LICENSE for
# details.
################################################################################

""" fifo IRC bot

A simple IRC bot that pipes a FIFO into an IRC chan.
"""

from __future__ import with_statement

from optparse import OptionParser
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.words.protocols import irc
from twisted.internet import error, reactor, ssl, threads
import os, os.path
import time
import sys

__version__ = "0.2"

class FifoIRC(irc.IRCClient):
  encoding = 'UTF-8'
  nickname = property(lambda self: self.factory.nickname)

  def __init__(self, *args, **kwargs):
    self.defered = None
    self.fd = None

  def sendLine(self, line):
    if isinstance(line, unicode):
      line = line.encode(self.encoding)
    return irc.IRCClient.sendLine(self, line)

  def signedOn(self):
    self.join(self.factory.channel)
    self.fd = os.open(self.factory.fifo, os.O_RDONLY | os.O_NONBLOCK)
    self.defered = threads.deferToThread(self.readFIFO)

  def connectionLost(self, reason):
    if self.defered is not None and self.fd is not None:
      os.close(self.fd)
      self.fd = None

  def readFIFO(self):
    # This is not really in the spirit of twisted. But I am not motiviated
    # enough to implement in a sane way.
    try:
      while True:
        d = os.read(self.fd, 1024)
        if not d:
          time.sleep(1)
          continue

        lines = d.split('\n')
        for line in lines:
          reactor.callFromThread(self.msg, self.factory.channel,
                                 line.rstrip('\n\r'))
    except OSError:
      pass

class FifoIRCFactory(ReconnectingClientFactory):
  protocol = FifoIRC

  def __init__(self, channel, nickname, fifo):
    self.channel = channel
    self.nickname = nickname
    self.fifo = fifo

  def buildProtocol(self, *args):
    print 'I: Connected.'
    self.resetDelay()
    return ReconnectingClientFactory.buildProtocol(self, *args)

  def clientConnectionLost(self, connector, reason):
    print 'I: Connection lost: %s' % (str(reason.getErrorMessage()), )
    return ReconnectingClientFactory.clientConnectionLost(self, connector,
                                                          reason)

  def clientConnectionFailed(self, connector, reason):
    print 'I: Connection failed: %s' % (str(reason.getErrorMessage()), )
    return ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                            reason)


def main(args=None):
  if args is None:
    args = sys.argv[1:]

  usage = 'usage: %prog [options] server chan'
  version = '%prog version ' + __version__

  parser = OptionParser(usage=usage, version=version)
  parser.add_option('--port', dest='port', type='int', default=6667)
  parser.add_option('-s', '--ssl', dest='ssl', action='store_true',
                    default=False)
  parser.add_option('--fifo', dest='fifo', type='string',
                    default='/tmp/ircfifo')
  parser.add_option('--create-fifo', dest='create_fifo', action='store_true',
                    default=False)
  parser.add_option('--nick', dest='nick', type='string', default='FifoIRC')
  parser.add_option('--bind', dest='bind_ip', type='string', default='')
  opts, args = parser.parse_args(args=args)
  if len(args) != 2:
    parser.print_usage()
    return 1

  bind_address = None
  if len(opts.bind_ip):
    bind_address = (opts.bind_ip, 0)

  if opts.create_fifo and not os.path.exists(opts.fifo):
    os.mkfifo(opts.fifo)
  if not os.path.exists(opts.fifo):
    print 'E: FiFo does not exist: %s' % opts.fifo
    return 1

  factory = FifoIRCFactory(args[1], opts.nick, opts.fifo)
  if opts.ssl:
    reactor.connectSSL(args[0], opts.port, factory, ssl.ClientContextFactory(),
                       bindAddress=bind_address)
  else:
    reactor.connectTCP(args[0], opts.port, factory, bindAddress=bind_address)

  try:
    reactor.run()
  except KeyboardInterrupt:
    reactor.stop()

  if opts.create_fifo:
    os.remove(opts.fifo)
  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))

# vim: set ts=2 sts=2 sw=2 et tw=80:
