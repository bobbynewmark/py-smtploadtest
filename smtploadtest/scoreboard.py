#Python BulitIns
import logging, cgi, os, json, time
from datetime import datetime
from collections import defaultdict
#External Modules
from twisted.web import server, resource

#we are going to do this stupid way right now
score_board = defaultdict(dict)

class AddScore(resource.Resource):
    isLeaf = 1

    def __init__(self, board):
        resource.Resource.__init__(self)
        self.board = board
        self.log = logging.getLogger("AddScore")
   
    def render_GET(self, request):        
        retval = {}
        self.log.debug(request.args)
        #get value from query string
        if "cid" in request.args:
            cid = request.args["cid"][0]
            obj = {}
            for key in request.args.keys():
                if key != "cid":
                    obj[key] = request.args[key][0]
            score_board[cid][time.time()] = obj
            retval["status"] = "OK"
        else:
            retval["status"] = "FAIL"
        return json.dumps(retval)

class Results(resource.Resource):
    isLeaf = 1
    
    def __init__(self, board):
        resource.Resource.__init__(self)
        self.board = board
        self.log = logging.getLogger("Results")
    
    def render_GET(self, request):
        return json.dumps(self.board)

def createSite():
    root = resource.Resource()
    root.putChild('add', AddScore(score_board))
    root.putChild('result', Results(score_board))
    return server.Site(root)
    
