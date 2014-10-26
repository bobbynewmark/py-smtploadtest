#Python BulitIns
import os, time, logging
from email.Header import Header
import email, json, sys, time, uuid

#External Modules
from twisted.mail import smtp, maildir
from twisted.web import server
from zope.interface import implements
from twisted.internet import protocol, reactor, defer, task
from twisted.web import client

class SinkMessage(object): 
    implements(smtp.IMessage)

    def __init__(self):
        self.logger = logging.getLogger("BaseMessage")
        self.lines = []
        self.FROM = ""    
                    
    def lineReceived(self, line):
        #self.logger.debug("lineRecieved")
        if line.lower().startswith("from:"):
            self.FROM = line.lower().replace("from:", "").strip()
        self.lines.append(line)

    def eomReceived(self):
        #self.logger.debug("eomReceived")  
        #self.logger.debug("self.FROM=%s" % self.FROM)  
        d = defer.Deferred()
        self.standardProcess(d)
        return d

    def standardProcess(self, d):
        msg = email.message_from_string("\n".join(self.lines))
        #Just sink that email
        cid = msg.get("to", "@").split("@")[0]
        obj_type = msg.get("subject")
        self.logger.debug("cid: %s len: %s", cid, len(msg.as_string()))
        client.getPage("http://localhost:8002/add?cid=%s&catch_time=%s" % (cid, time.time()) )

        #with open("/temp/bp/" + str(uuid.uuid4()) + ".txt", "w") as f:
        #    f.write(msg.as_string())   

        return d.callback("finished")

    def connectionLost(self):
        self.logger.debug("connectionLost")
        del(self.lines)
        self.FROM = ""

class LocalDelivery(object): 
    implements(smtp.IMessageDelivery)

    def __init__(self):
        self.logger = logging.getLogger("LocalDelivery")

    def receivedHeader(self, helo, orgin, recipents):
        myHostname, clientIP = helo
        headerValue = "by %s from %s with ESMTP; %s" % (
            myHostname, clientIP, smtp.rfc822date())
        retval = "Recieved: %s" % Header(headerValue)
        #retval = ""
        self.logger.debug("receivedHeader: helo:%s orgin:%s recipents:%s", helo, orgin, [r.dest for r in recipents] )
        return retval

    def validateTo(self, user):
        self.logger.debug("validateTo: %s", user)
        return lambda: SinkMessage()

    def validateFrom(self, helo, orginAddress):
        self.logger.debug("validateFrom: helo:%s orginAddress:%s", helo, orginAddress)
        return orginAddress

class SMTPFactory(protocol.ServerFactory):

    def __init__(self, delivery):
        self.delivery = delivery
        self.logger = logging.getLogger("SMTPFactory")
    
    def buildProtocol(self, addr):
        self.logger.debug("Setting up protocol")
        smtpProtocol = smtp.SMTP(self.delivery)
        smtpProtocol.factory = self
        return smtpProtocol