# This file based on final example at http://docs.python.org/library/email-examples.html

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(from_addr, to_addr, subject, msg_txt, msg_html=None):
	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = from_addr
	msg['To'] = to_addr
	
	part1 = MIMEText(msg_txt, 'plain')
	msg.attach(part1)
	
	if msg_html is not None:
		part2 = MIMEText(msg_html, 'html')
		msg.attach(part2)
	
	s = smtplib.SMTP('localhost')
	s.sendmail(from_addr, to_addr, msg.as_string())
	s.quit()
