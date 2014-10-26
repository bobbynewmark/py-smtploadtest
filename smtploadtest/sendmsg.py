#Python BulitIns
import smtplib
import sys
import email
import time

def send_msg_from_file(server, port, use_tls, password, subject_replacements, email_path):
    msg = None
    with open(email_path) as f:
        msg = email.message_from_file(f)
    return send_msg(server, port, use_tls, password, subject_replacements, msg)

def send_msg_from_string(server, port, use_tls, password, subject_replacements, email_str):
    msg = None
    msg = email.message_from_string(email_str)	
    return send_msg(server, port, use_tls, password, subject_replacements, msg)
    
def send_msg(server, port, use_tls, password, subject_replacements, msg):	
    sender = msg["From"]
    recipient = msg["To"]
    if subject_replacements:
        subject = msg["Subject"]
        subject = subject % tuple(subject_replacements)
        del msg["Subject"]
        msg["Subject"] = subject
    
    t1 = time.time()
    session = smtplib.SMTP(server, port)
    #session.set_debuglevel(1)
    if use_tls:
        session.starttls()
    session.helo()
    if password:
        session.login(sender, password)
    session.sendmail(sender, recipient, msg.as_string())
    session.quit()
    return time.time() - t1

if __name__ == "__main__":
    subject_replacements = []
    if len(sys.argv) > 4:
        subject_replacements = sys.argv[5:]
    send_msg_from_file(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])