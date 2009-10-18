from twisted.application import internet, service
from twisted.cred import credentials, strcred
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.web import server
from zope.interface import implements

import bnd


class Options(usage.Options, strcred.AuthOptionMixin):
    supportedInterfaces = (credentials.IUsernamePassword, )

    optParameters = [
        ('channel', 'c', '#commits', 'IRC channel'),
        ('nick', 'n', 'Raboof', 'IRC nickname'),
        ('port', 'p', 7009, 'port of XML-RPC server'),
        ('ircport', None, 6667, 'port of IRC server'),
        ('server', 's', 'localhost', 'IRC server')
    ]


class BNDMaker(object):
    implements(service.IServiceMaker, IPlugin)

    tapname = 'bnd'
    description = 'The Git commit bot.'
    options = Options

    def makeService(self, options):
        interface = options['credInterfaces'][credentials.IUsernamePassword][0]
        login_checker = bnd.LoginChecker(interface)

        bot = service.MultiService()
        xmlrpcinterface = bnd.XMLRPCInterface(bot, login_checker)
        rpc = internet.TCPServer(options['port'], server.Site(xmlrpcinterface))
        rpc.setName('XML-RPC')
        rpc.setServiceParent(bot)
        ircbot = internet.TCPClient(options['server'], options['ircport'],
                                    bnd.BNDFactory(xmlrpcinterface,
                                    options['channel'], options['nick']))
        ircbot.setName('IRC')
        ircbot.setServiceParent(bot)

        return bot


serviceMaker = BNDMaker()
