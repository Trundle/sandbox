""" fifo IRC bot

A simple IRC bot that pipes a FIFO into an IRC chan.
"""

from __future__ import with_statement

from twisted.internet import protocol
from twisted.words.protocols import irc
from twisted.internet import reactor, threads
from twisted.protocols.basic import FileSender, LineReceiver
import time

class FifoIRC(irc.IRCClient):
  encoding = 'UTF-8'
  nickname = property(lambda self: self.factory.nickname)

  def __init__(self, *args, **kwargs):
    self.defered = None
    self.open_fifo = None

  def sendLine(self, line):
    if isinstance(line, unicode):
      line = line.encode(self.encoding)
    return irc.IRCClient.sendLine(self, line)

  def signedOn(self):
    self.join(self.factory.channel)
    self.defered = threads.deferToThread(self.readFIFO)

  def connectionLost(self, reason):
    if self.defered is not None and self.open_fifo is not None:
      self.open_fifo.close()

  def readFIFO(self):
    # This is not really in the spirit of twisted. But I am not motiviated
    # enough to implement in a sane way.
    try:
      with open(self.factory.fifo, 'r') as self.open_fifo:
        while True:
          line = self.open_fifo.readline()
          if not line:
            time.sleep(1)
            continue
          reactor.callFromThread(self.msg, self.factory.channel,
                                 line.rstrip('\n\r'))
    except OSError:
      pass

class FifoIRCFactory(protocol.ClientFactory):
    protocol = FifoIRC

    def __init__(self, channel, nickname, fifo):
        self.channel = channel
        self.nickname = nickname
        self.fifo = fifo

def main(host, port, channel, nick, fifo):
  reactor.connectTCP(host, port, FifoIRCFactory(channel, nick, fifo))
  reactor.run()

main('someserver', 6667 , '#wah', 'foobar', '/tmp/bla')
