#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author    : 奶权
# Action    : 微博监控
# Desc      : 微博监控启动模块

import weiboMonitor,time,hashlib,requests
import smtplib
import base64
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header

def getMd5(str):
        m = hashlib.md5()
        m.update(str)
        return m.hexdigest()

def downloadImg(imgSrc):
    r = requests.get(imgSrc.strip())
    fileName = getMd5(imgSrc) + '.png'
    with open('images/' + fileName, 'wb') as f:
        f.write(r.content)
    return 'images/' + fileName

def sendMail(dicts):
    flag = True
    _user = "" #发件人
    _pwd  = "" #授权码
    _to   = "" #收件人
    try:
        text = u'发送时间: '+dicts['created_at']+u'<br>'
        text += u'发送内容: <br>'+dicts['text']+u'<br>'
        if dicts.has_key('picUrls'):
            for pic in dicts['picUrls']:
                imgFile = downloadImg(pic)
                f = open(imgFile,'rb')
                baseCode = base64.b64encode(f.read())
                text += u'<img src="data:image/png;base64,%s">'%baseCode
        text += u'<br>来自: '+dicts['source']

        msg=MIMEText(text.encode('utf-8'),'html','utf-8')
        msg['Subject']=u"货来啦~ 您监控的微博用户"+dicts['nickName']+u"发布微博啦"
        msg['Form'] = formataddr(["微博监控系统",_user])
        msg['To'] = formataddr(["微博监控系统",_to])
        print msg.as_string()
        server = smtplib.SMTP_SSL('smtp.qq.com',465)
        server.login(_user,_pwd)
        server.sendmail(_user, _to, msg.as_string())
        server.quit()
    except Exception as e:
        print e
        flag = False
    return flag

def main(username,password,wbUserId):
    w = weiboMonitor.weiboMonitor()
    w.login(username,password)
    w.getWBQueue(wbUserId)
    while 1:
        newWB = w.startMonitor()
        if newWB is not None:
            print sendMail(newWB)
        time.sleep(3)

if __name__ == '__main__':
    username = input('Please input your username : ')
    password = raw_input('Please input your password : ')
    wbUserId = input('Please input the weibo user id you want to monitor : ')
    main(username,password,wbUserId)
