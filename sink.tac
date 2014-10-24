from smtploadtest import emailsink, scoreboard
from twisted.application import service, internet
import logging

class SinkDaemon(object):
    
    def __init__(self, configPath = ""):
        logger = logging.getLogger("")
        logger.setLevel(logging.DEBUG) 
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        self.logger = logging.getLogger("SinkDaemon")
        self.mailDelivery = emailsink.LocalDelivery()
        self.mailFactory = emailsink.SMTPFactory(self.mailDelivery)
        self.mailPort = 8001
        self.mailInterface = ""     
        self.score_board = scoreboard.createSite()
        self.webPort = 8002
        self.webInterface = ""
        

application = service.Application("emailsink")

daemon = SinkDaemon()

mailService = internet.TCPServer(daemon.mailPort,
                                 daemon.mailFactory,
                                 interface=daemon.mailInterface)
mailService.setName("mailService")
mailService.setServiceParent(application)

webService = internet.TCPServer(daemon.webPort,
                                 daemon.score_board,
                                 interface=daemon.webInterface)
webService.setName("webService")
webService.setServiceParent(application)