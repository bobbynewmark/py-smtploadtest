from twisted.application import service
from smtploadtest.twistedPitcher import Pitcher, PitcherConfig, PitcherService
import logging

application = service.Application("Pitcher")
logger = logging.getLogger("")
logger.setLevel(logging.DEBUG) 
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

application = service.Application("emailpitcher")
p = Pitcher(PitcherConfig("config.json"))
ps = PitcherService(p)
ps.setName("pitcherService")
ps.setServiceParent(application)



