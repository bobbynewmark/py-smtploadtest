#Python BulitIns
import os, time, logging, mimetypes
from email.Header import Header
import email, json, sys, time, uuid
from HTMLParser import HTMLParser

#External Modules
from twisted.mail import smtp, maildir
from twisted.web import server
from zope.interface import implements
from twisted.internet import protocol, reactor, defer, task
from twisted.web import client

def noop(*args):
    return 

class QuickParser(HTMLParser):

    def __init__(self):
        self.first_img_src = ""
        self.first_link_href = ""
        HTMLParser.__init__(self)
        self.logger = logging.getLogger("QuickParser")
    
    def handle_starttag(self, tag, attrs):
        #self.logger.debug("%s:%s" % tag, attrs)
        if tag == "img" and not self.first_img_src:
            srcs = [item[1] for item in attrs if item[0] == "src" and item[1].lower().startsWith("http://") ]
            if srcs:
                self.first_img_src = srcs[0]
        elif tag == "a" and not self.first_link_href:
            hrefs = [item[1] for item in attrs if item[0] == "href" and item[1].lower().startsWith("http://")]
            if hrefs:
                self.first_link_href = hrefs[0]
        #ignoreing everything else

class EmailProcessor(object):
    def __init__(self, lines):
        self.lines = lines
        self.logger = logging.getLogger("EmailProcessor")

    def process(self):
        d = defer.Deferred()
        d.addCallback(self.read_msg)
        d.addCallback(self.add_to_scoreboard)
        d.addCallback(self.load_tracking_link)
        d.addCallback(self.click_link)
        d.callback("DONE")
        return d

    def read_msg(self, *args):
        self.msg = email.message_from_string("\n".join(self.lines))
        self.cid = self.msg.get("to", "@").split("@")[0]
        self.logger.debug("cid: %s", self.cid)
        self.htmlpart = ""
        for part in self.msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            ext = mimetypes.guess_extension(part.get_content_type())
            #self.logger.debug(ext)    
            if (ext == ".html"):
                #self.logger.debug("found html")    
                self.htmlpart = part.get_payload(decode=1)
                break

        if self.htmlpart:
            qp = QuickParser()
            qp.feed(self.htmlpart)
            self.tracking_img = qp.first_img_src
            self.link = qp.first_link_href
        
    def add_to_scoreboard(self, *args):        
        client.getPage("http://localhost:8002/add?cid=%s&catch_time=%s" % (self.cid, time.time()))
        #d.addCallback(noop, noop)
        #return d

    def load_tracking_link(self, *args):
        if self.tracking_img:
            self.logger.debug(self.tracking_img)
            client.getPage(self.tracking_img)
        else:
            self.logger.debug("No Tracking")

    def click_link(self, *args):
        if self.link:
            self.logger.debug(self.link)
            client.getPage(self.link)
        else:
            self.logger.debug("No Link")
   

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
        ep = EmailProcessor(self.lines)
        return ep.process()

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
