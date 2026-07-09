# -*- coding: utf-8 -*-
"""
Created on Sun Dec  4 01:38:51 2016

@author: Redouanelg
"""
import copy
import pdb
from collections import OrderedDict
from multiprocessing.managers import BaseManager
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import pdb


#pdb.set_trace()
mail_host="smtp.qq.com"
mail_user="627710785@qq.com"
mail_pass="lhs0626WEN."

sender='627710785@qq.com'
receivers=['1159528095@qq.com']
message=MIMEText('python 邮件发送测试','plain','utf-8')
message['From']=Header('aa','utf-8')
message['To']=Header('text','utf-8')

subject='python text'
message['Subject']=Header(subject,'utf-8')
pdb.set_trace()
try:
    smtpObj=smtplib.SMTP()
    smtpObj.connect(mail_host,587)
    smtpObj.login(mail_user,mail_pass)
    smtpObj.sendmail(sender,receivers,message.as_string())
    print("success")
except smtplib.SMTPException:
    print("Error")    






#import json
#file="H:\\Aviso\\yuanliming\\20151230new\\json\\20151230\\eddy_info_merge20151230.json"
#temporaryfile=open(file)
#file=json.load(temporaryfile)
#temporaryfile.close()
#for i in file:
#    if i=="eddy_0.625_-34.125":
#        print(file[i])