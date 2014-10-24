from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email import Charset
from paragraphs import give_me_text
import os
import random
import hashlib
import time
import sys

def make_me_msg(me, you, subject, preamble, postamble, text_size, attachments):
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = you
        
    text = preamble + "\n\n" + give_me_text(text_size, "", "\n\n") + postamble
    html = "<html><head></head><body><p>%s</p></body></html>" % text.replace("\n\n", "</p><p>")
    msg.attach(MIMEText(text, 'plain','utf-8'))
    msg.attach(MIMEText(html, 'html', 'utf-8'))
        
    for attachment in attachments:
        filepath, type, params = attachment
        fp = open(filepath, 'rb')
        if type == "image":
            i = MIMEImage(fp.read());
            for key,value in params.items():
                i.add_header(key,value)
            msg.attach(i)
        fp.close()
    
    return msg
    
    
def create_hash():
    return hashlib.sha1(str(time.time()) + str(random.random())).hexdigest()[:10]
    
def create_corpus(froms, you_domain, subject, preamble, postamble, text_size, percent_with_attachment, attachments, save_loc, amount):
        
    with_attachment = int(amount * percent_with_attachment)
    without_attachment = amount - with_attachment
    
    for i in xrange(without_attachment):
        cid = create_hash()
        msg = make_me_msg(random.choice(froms), cid + "@" + you_domain, subject, preamble, postamble, text_size, [])
        f = open( os.path.join(save_loc, cid + '.eml'), 'w');
        f.write(msg)
        f.close()
        
    for i in xrange(with_attachment):
        cid = create_hash()
        msg = make_me_msg(random.choice(froms), cid + "@" + you_domain, subject, preamble, postamble, text_size, [ random.choice(attachments) ] )
        f = open( os.path.join(save_loc, cid + '.eml'), 'w');
        f.write(msg.as_string())
        f.close()
    
if __name__ == "__main__":
    froms_file, you_domain, attachments_file, save_loc, amount = sys.argv[1:6]
    
    amount = int(amount)	
    
    froms = []
    if os.path.exists(froms_file):
        f = open(froms_file)
        froms = filter(lambda x: bool(x), f.read().split("\n"))
        f.close()
    
    attachments = []
    if os.path.exists(attachments_file):
        f = open(attachments_file)
        attachments = map(lambda y: (y,"image"), filter(lambda x: bool(x), f.read().split("\n")))
        f.close()
    
    create_corpus(froms, you_domain, "I am a flood", "Hi,", "From your flood", 1000, 0, attachments, save_loc, amount)
    