from twisted.internet import reactor
from twisted.internet import task
from twisted.internet.defer import DeferredList
import createmsg
import sendmsg
import time
import urllib
import logging
import json
import random

class PitcherConfig(object):
    def __init__(self, filename):

        rawconfig = {}
        with open(filename) as f:
            rawconfig = json.load(f)


        self.scoreboard_url = rawconfig["scoreboard_url"]
        if rawconfig["email_from_file"]:
            with open(rawconfig["email_from_file"]) as f:
                self.email_from = [line.strip() for line in f.readlines() if line.strip()]
        else:
            self.email_from = rawconfig["email_from"]
        self.to_domain = rawconfig["to_domain"]
        self.subject = rawconfig["subject"]
        self.preamble = rawconfig["preamble"]
        self.postamble = rawconfig["postamble"]
        self.text_size = rawconfig["text_size"]
        self.attachments = rawconfig["attachments"]
        self.smtp_ip = rawconfig["smtp_ip"]
        self.smtp_port = rawconfig["smtp_port"]
        self.inital_wait = rawconfig["inital_wait"]
        self.pitches_per_min = rawconfig["pitches_per_min"]
        self.length_in_mins = rawconfig["length_in_mins"]


class Pitcher(object):
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("Pitcher")
        
    
    def	pitch(self, ball, smtp_ip, smtp_port):
        self.logger.debug("pitching")
        timing = sendmsg.send_msg(smtp_ip, smtp_port, False, None, None, ball["msg"])
        return timing

    def send_to_scoreboard(self,base_url, cid, time_taken):
        t1 = time.time()
        f = urllib.urlopen(base_url + "/add?cid=%s&pitch_time=%s" % (cid, time_taken))
        f.read() #TODO: Check result
        f.close()
        self.logger.debug("send_to_scoreboard, %s", time.time()-t1)
    
    def innings(self,pitches_per_min=0, length_in_mins=0):
        pitches_per_min = pitches_per_min or self.config.pitches_per_min
        length_in_mins = length_in_mins or self.config.length_in_mins
        self.logger.info("Innings Start")
        self.logger.info("Waiting %s secs before start" % self.config.inital_wait)
        sleep_s = 60.0 / pitches_per_min
        self.logger.debug("pitch sleep: %s", sleep_s)
        total_pitches = max(int(pitches_per_min * length_in_mins), 1)
        self.logger.debug("Total pitches: %s",total_pitches);
        
        defereds = []
        for i in range(total_pitches):
            
            defereds.append(task.deferLater(reactor, (i*sleep_s)+self.config.inital_wait, self.action, i))

        dl = DeferredList(defereds)
        dl.addCallback(self.end)

    def action(self, i):
        
        t1 = time.time()
        ball = self.get_ball(i)
        try:
            time_taken = self.pitch(ball, self.config.smtp_ip, self.config.smtp_port)
            self.send_to_scoreboard(self.config.scoreboard_url, ball["cid"], time_taken)
        except:
            self.logger.error("PITCH FAIL!!!")
        

    def end(self, result):
        self.logger.info("Finished")
        reactor.stop()
        
    def get_ball(self, i):
        try:
            t1 = time.time()
            cid = createmsg.create_hash()
            t2 = time.time()
            efrom = random.choice(self.config.email_from) #TODO: weighted
            attachments = map(lambda y: y[:3], filter( lambda x :(x[3]*i)%1 == 0, self.config.attachments))
            msg = createmsg.make_me_msg(
                efrom,
                cid+self.config.to_domain,   
                self.config.subject, 
                self.config.preamble, 
                self.config.postamble % {"efrom":efrom, "i":i},
                self.config.text_size, 
                attachments)
            t3 = time.time()
            self.logger.debug("hash: %s msg: %s", t2-t1, t3-t2)
            return { "cid" : cid, "msg" : msg }
        except Exception as e:
            self.logger.error("Exception %s" % e)
            raise e
        



