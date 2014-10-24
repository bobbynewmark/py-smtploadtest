import createmsg
import sendmsg
import time
import urllib
import logging

logger = logging.getLogger("")
logger.setLevel(logging.DEBUG) 
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

class Pitcher(object):

	def __init__(self):
		self.scoreboard_url = "http://localhost:8002"
		self.email_from = ""
		self.to_domain = ""
		self.subject = "Hey There"
		self.preamble = ""
		self.postamble = ""
		self.text_size = 1000
		self.attachments = []
		self.smtp_ip = "127.0.0.1"
		self.smtp_port = 8001
		self.logger = logging.getLogger("Pitcher")
		
	
	def	pitch(self, ball, smtp_ip, smtp_port):
		timing = sendmsg.send_msg(smtp_ip, smtp_port, False, None, None, ball["msg"])
		return timing

	def send_to_scoreboard(self,base_url, cid, time_taken):
		t1 = time.time()
		f = urllib.urlopen(base_url + "/add?cid=%s&pitch_time=%s" % (cid, time_taken))
		f.read() #TODO: Check result
		f.close()
		self.logger.debug("send_to_scoreboard, %s", time.time()-t1)
	
	def innings(self,pitches_per_min, length_in_mins):
		self.logger.info("Innings Start")
		sleep_s = 60.0 / pitches_per_min
		self.logger.debug("pitch sleep: %s", sleep_s)
		total_pitches = pitches_per_min * length_in_mins
		
		while total_pitches:
			t1 = time.time()
			ball = self.get_ball()
			time_taken = self.pitch(ball, self.smtp_ip, self.smtp_port)
			#self.send_to_scoreboard(self.scoreboard_url, ball["cid"], time_taken)
			total_pitches -= 1
			self.logger.info("pitch: cid:%s time_taken:%s", ball["cid"], time_taken)
			t2 = time.time() - t1
			if (t2 < sleep_s):
				self.logger.debug("sleeping for %s", sleep_s-t2) 
				time.sleep(sleep_s-t2)
			else:
				self.logger.debug("no sleep %s", t2)
			
			
		self.logger.info("Innings End") 
		
	def get_ball(self):
		t1 = time.time()
		cid = createmsg.create_hash()
		t2 = time.time()
		msg = createmsg.make_me_msg(
			self.email_from, 
			cid+self.to_domain, 
			self.subject, 
			self.preamble, 
			self.postamble, 
			self.text_size, 
			self.attachments)
		t3 = time.time()
		self.logger.debug("hash: %s msg: %s", t2-t1, t3-t2)
		return { "cid" : cid, "msg" : msg }


	

	
