#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import smtplib
from email.mime.text import MIMEText

#                            Main function
#-----------------------------------------------------------------------------#

def send_email(body, sender_password, subject="Your script has finished!", sender="wikiclassify@gmail.com", receiver="wikiclassify@gmail.com"):
    if sender_password:
        print("Sending email...",end="\r")
        try:    
            msg = MIMEText(body)
    
            msg['Subject'] = subject
            msg['From'] = sender  
            msg['To'] =  reciever
    
            s = smtplib.SMTP('smtp.gmail.com',587)
            s.ehlo()
            s.starttls()
            s.login(sender, sender_password)
            s.sendmail(sender, [reciever], msg.as_string())
            print("\tEmail sent.")
        
        except:
            print("\tEmail failed.")
    else:
        print(body)