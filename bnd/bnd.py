# Dear Python, I really like to use encoding=utf-8 in that file.

"""
    bnd
    ~~~

    A simple commit message messaging bot.

    Copyright (C) by the #cdt development team.
"""

from twisted.cred.credentials import UsernamePassword
from twisted.internet import protocol
from twisted.internet.defer import maybeDeferred
from twisted.web import http, xmlrpc
from twisted.web.server import NOT_DONE_YET
from twisted.words.protocols import irc


class LoginChecker(object):
    def __init__(self, interface):
        self.interface = interface

    def check(self, username, password):
        credential = UsernamePassword(username, password)
        return maybeDeferred(self.interface.requestAvatarId, credential)


class XMLRPCInterface(xmlrpc.XMLRPC):
    def __init__(self, service, login_checker, *args, **kwargs):
        xmlrpc.XMLRPC.__init__(self, *args, **kwargs)
        self.login_checker = login_checker
        self.service = service

    def login_failed(self, failure, request):
        request.setResponseCode(http.UNAUTHORIZED)
        request.write('Authorization required.')
        request.finish()

    def real_render_POST(self, login_result, request):
        return xmlrpc.XMLRPC.render_POST(self, request)

    def render_POST(self, request):
        deferred = self.login_checker.check(request.getUser(),
                                            request.getPassword())
        deferred.addCallback(self.real_render_POST, request)
        deferred.addErrback(self.login_failed, request)
        return NOT_DONE_YET

    def xmlrpc_say(self, channel, message):
        self.client.msg(channel, message)
        return True


class BND(irc.IRCClient):
    encoding = 'iso-8859-15'
    nickname = property(lambda self: self.factory.nickname)

    def sendLine(self, line):
        if isinstance(line, unicode):
            line = line.encode(self.encoding)
        return irc.IRCClient.sendLine(self, line)

    def signedOn(self):
        self.join(self.factory.channel)


class BNDFactory(protocol.ClientFactory):
    protocol = BND

    def __init__(self, xmlrpcinterface, channel, nickname='Raboof'):
        self.xmlrpcinterface = xmlrpcinterface
        self.channel = channel
        self.nickname = nickname

    def buildProtocol(self, addr):
        p = protocol.ClientFactory.buildProtocol(self, addr)
        self.xmlrpcinterface.client = p
        return p
