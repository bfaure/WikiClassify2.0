import smtplib
from email.mime.text import MIMEText
import sys

# command line call should be "python email_agent.py <destination>""

def main():

	if len(sys.argv)==2:
		print("Sending email...",end="\r")
		reciever = sys.argv[1]

		msg = MIMEText(" ")

		sender = "wikiclassify@gmail.com"
		sender_password = "wikipassword"

		msg['Subject'] = "WikiClassify parser is complete" # subject line
		msg['From'] = sender  
		msg['To'] =  reciever

		s = smtplib.SMTP('smtp.gmail.com',587)
		s.ehlo()
		s.starttls()
		s.login(sender,sender_password)
		s.sendmail(sender, [reciever], msg.as_string())
		print("Sending email... sent.")
		return

	if len(sys.argv)==3:
		print("Sending email...",end="\r")
		reciever = sys.argv[1]
		body = sys.argv[2].split("+")
		lines = ""
		for line in body:
			items = line.split("-")
			lines += items[0]+": "+items[1]+"\n"

		msg = MIMEText(lines)

		sender = "wikiclassify@gmail.com"
		sender_password = "wikipassword"

		msg['Subject'] = "WikiClassify parser is complete" # subject line
		msg['From'] = sender  
		msg['To'] =  reciever

		s = smtplib.SMTP('smtp.gmail.com',587)
		s.ehlo()
		s.starttls()
		s.login(sender,sender_password)
		s.sendmail(sender, [reciever], msg.as_string())
		print("Sending email... sent.")
		return

	print("Did not provide destination email address")

if __name__ == '__main__':
	main()
