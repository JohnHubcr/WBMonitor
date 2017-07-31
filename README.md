# Python系列之——利用Python实现微博监控

#### 0x00 前言:
![素材](http://i1.ciimg.com/602361/6d42627539f48ec3.png)前几个星期在写一个微博监控系统 可谓是一波三折啊 获取到微博后因为一些字符编码问题 导致心态爆炸开发中断 但是就在昨天发现了另外一个微博的接口  

一个手机微博的接口https://m.weibo.cn/ 经过一番测试后认为这个接口满足我的要求 就继续完成未完成的使命吧

#### 0x01 分析:
![素材](http://i1.ciimg.com/602361/3556aed5a00277f2.png)这个接口直接访问的话会有一个302跳转到一个登陆界面  
![Markdown](http://i1.ciimg.com/602361/7750485844244155.png)
也就是说这里需要先模拟登陆一下才可以访问到微博  
抓个包分析了一下  
![Markdown](http://i1.ciimg.com/602361/1c5a2cc87e05b64c.png)
发现只要用户名和密码正确既返回200且json部分的retcode会返回20000000  
![素材](http://i1.ciimg.com/602361/a2cd14dc4bb4edb5.png)少了验证码这一大坑 那模拟登陆就相当简单啦  

登陆完后访问用户主页 例如:https://m.weibo.cn/u/3023940914  
可以在审查元素的Network模块看到 这里用了两个xhr来加载用户信息及微博信息  
![Markdown](http://i2.tiimg.com/602361/926e38139300a5bf.png)
![素材](http://i1.ciimg.com/602361/12f1bfeafeba4a7a.png)分别是  
https://m.weibo.cn/api/container/getIndex?type=uid&value=3023940914&containerid=1005053023940914  
https://m.weibo.cn/api/container/getIndex?type=uid&value=3023940914&containerid=1076033023940914  
经过测试这个接口直接加上**type**和**value**参数访问 就相当于第一个接口 不必加上**containerid**参数  
而第二个接口的**containerid**参数则是通过第一个接口获取的  

![素材](http://i1.ciimg.com/602361/3556aed5a00277f2.png)获取到第二个**containerid**参数访问第二个接口就可以获取到这个**uid**发布的微博了  
![Markdown](http://i1.ciimg.com/602361/70c99f77d40bf8ed.png)
返回的是json格式的数据 用户的微博信息都在**cards**列表里每条数据的**mblog**数组里面 包括**微博正文、图片、来源与时间**等  
![素材](http://i1.ciimg.com/602361/acef3c6c9e7e700e.png)其中**card_type**标识的是微博类型 例如:文字微博 图片微博 视频微博 转发等 经过测试文字微博和图片微博的**card_type**标识都一样为9  

这里初步只开发监控文字和图片微博的功能```<del>其实就是懒</del>```  

#### 0x02 开发
![素材](http://i1.ciimg.com/602361/6869750adb42eee2.png)首先需要模拟登陆 后续的操作都需要基于登陆的格调来进行 也是需要在同个会话进行 可以使用**requests.session()** 方法来完成  
代码片段:
```Python
reqHeaders = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://passport.weibo.cn/signin/login',
    'Connection': 'close',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
}
loginApi = 'https://passport.weibo.cn/sso/login'
loginPostData = {
    'username':userName,
    'password':passWord,
    'savestate':1,
    'r':'',
    'ec':'0',
    'pagerefer':'',
    'entry':'mweibo',
    'wentry':'',
    'loginfrom':'',
    'client_id':'',
    'code':'',
    'qq':'',
    'mainpageflag':1,
    'hff':'',
    'hfp':''
}
#get user session
session = requests.session()
try:
    r = session.post(loginApi,data=loginPostData,headers=reqHeaders)
    if r.status_code == 200 and json.loads(r.text)['retcode'] == 20000000:
        #successful
        #do someting
    else:
        #Logon failure!
except Exception as e:
    #Logon failure!
```
![素材](http://i1.ciimg.com/602361/3b9a86501a0ae30b.png)登陆完成后就可以拼接用户id访问前面说的第一个接口了  
访问完后再拼接**containerid**参数获取微博信息的json数据  
代码片段:
```Python
#get user weibo containerid
userInfo 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s'%(wbUserId,wbUserId)
try:
    r = session.get(userInfo,headers=reqHeaders)
    for i in r.json()['tabsInfo']['tabs']:
        if i['tab_type'] == 'weibo':
            conId = i['containerid']
except Exception as e:
    #failure!
#get user weibo index
weiboInfo = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s&containerid=%s'%(wbUserId,wbUserId,conId)
try:
    r = session.get(weiboInfo,headers=reqHeaders)
    itemIds = []   #WBQueue
    for i in r.json()['cards']:
        if i['card_type'] == 9:
            itemIds.append(i['mblog']['id'])
except Exception as e:
    #failure!
```
![素材](http://i1.ciimg.com/602361/565c21f8e0a660b1.png)这里把所有获取到的微博的id存起来 后面继续访问是发现有新的微博id不在这个列表里就证明是新发布的微博  
代码片段:  
```Python
def startMonitor():
      returnDict = {}
      try:
          r = session.get(weiboInfo,headers=reqHeaders)
          for i in r.json()['cards']:
              if i['card_type'] == 9:
                  if str(i['mblog']['id']) not in itemIds:
                      itemIds.append(i['mblog']['id'])
                      #Got a new weibo
                      #@ return returnDict dict
                      returnDict['created_at'] = i['mblog']['created_at']
                      returnDict['text'] = i['mblog']['text']
                      returnDict['source'] = i['mblog']['source']
                      returnDict['nickName'] = i['mblog']['user']['screen_name']
                      #if has photos
                      if i['mblog'].has_key('pics'):
                          returnDict['picUrls'] = []
                          for j in i['mblog']['pics']:
                              returnDict['picUrls'].append(j['url'])
                      return returnDict
      except Exception as e:
          #failure!
```
![素材](http://i1.ciimg.com/602361/8b469fd0042a4908.png)将这些方法封装成了一个类 完整代码如下  
```Python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author    : 奶权
# Action    : 微博监控
# Desc      : 微博监控主模块

import requests,json,sys
from lxml import etree

class weiboMonitor():
    """
        @   Class self  :
    """
    def __init__(self, ):
        self.session = requests.session()
        self.reqHeaders = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://passport.weibo.cn/signin/login',
            'Connection': 'close',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
        }

    """
        @   Class self  :
        @   String userName  : The username of weibo.cn
        @   String passWord  : The password of weibo.cn
    """
    def login(self, userName, passWord):
        loginApi = 'https://passport.weibo.cn/sso/login'
        loginPostData = {
            'username':userName,
            'password':passWord,
            'savestate':1,
            'r':'',
            'ec':'0',
            'pagerefer':'',
            'entry':'mweibo',
            'wentry':'',
            'loginfrom':'',
            'client_id':'',
            'code':'',
            'qq':'',
            'mainpageflag':1,
            'hff':'',
            'hfp':''
        }
        #get user session
        try:
            r = self.session.post(loginApi,data=loginPostData,headers=self.reqHeaders)
            if r.status_code == 200 and json.loads(r.text)['retcode'] == 20000000:
                self.echoMsg('Info','Login successful! UserId:'+json.loads(r.text)['data']['uid'])
            else:
                self.echoMsg('Error','Logon failure!')
                sys.exit()
        except Exception as e:
            self.echoMsg('Error',e)
            sys.exit()

    """
        @   Class self  :
        @   String wbUserId  : The user you want to monitored
    """
    def getWBQueue(self, wbUserId):
        #get user weibo containerid
        userInfo = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s'%(wbUserId,wbUserId)
        try:
            r = self.session.get(userInfo,headers=self.reqHeaders)
            for i in r.json()['tabsInfo']['tabs']:
                if i['tab_type'] == 'weibo':
                    conId = i['containerid']
        except Exception as e:
            self.echoMsg('Error',e)
            sys.exit()
        #get user weibo index
        self.weiboInfo = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s&containerid=%s'%(wbUserId,wbUserId,conId)
        try:
            r = self.session.get(self.weiboInfo,headers=self.reqHeaders)
            self.itemIds = []   #WBQueue
            for i in r.json()['cards']:
                if i['card_type'] == 9:
                    self.itemIds.append(i['mblog']['id'])
            self.echoMsg('Info','Got weibos')
            self.echoMsg('Info','Has %d id(s)'%len(self.itemIds))
        except Exception as e:
            self.echoMsg('Error',e)
            sys.exit()
    """
        @   Class self  :
    """
    def startMonitor(self, ):
        returnDict = {}
        try:
            r = self.session.get(self.weiboInfo,headers=self.reqHeaders)
            for i in r.json()['cards']:
                if i['card_type'] == 9:
                    if str(i['mblog']['id']) not in self.itemIds:
                        self.itemIds.append(i['mblog']['id'])
                        self.echoMsg('Info','Got a new weibo')
                        #@ return returnDict dict
                        returnDict['created_at'] = i['mblog']['created_at']
                        returnDict['text'] = i['mblog']['text']
                        returnDict['source'] = i['mblog']['source']
                        returnDict['nickName'] = i['mblog']['user']['screen_name']
                        #if has photos
                        if i['mblog'].has_key('pics'):
                            returnDict['picUrls'] = []
                            for j in i['mblog']['pics']:
                                returnDict['picUrls'].append(j['url'])
                        return returnDict
            self.echoMsg('Info','Has %d id(s)'%len(self.itemIds))
        except Exception as e:
            self.echoMsg('Error',e)
            sys.exit()

    """
        @   String level   : Info/Error
        @   String msg     : The message you want to show
    """
    def echoMsg(self, level, msg):
        if level == 'Info':
            print '[Info] %s'%msg
        elif level == 'Error':
            print '[Error] %s'%msg

```
![素材](http://i1.ciimg.com/602361/12f1bfeafeba4a7a.png)写了个一发现有新微博就发邮件提醒的功能 完整代码见Github地址 [https://github.com/naiquann/WBMonitor](https://github.com/naiquann/WBMonitor)  
#### 0x03 测试  
![素材](http://i1.ciimg.com/602361/5b5dd2f6476c629e.png)运行代码  
![Markdown](http://i2.tiimg.com/602361/6414331da5040752.png)  
填写完相关的登陆信息及要监控的用户的id后  
![Markdown](http://i2.tiimg.com/602361/4c933175b8562773.png)  
![素材](http://i1.ciimg.com/602361/6d42627539f48ec3.png)这里写了一个心跳包 每三秒访问一次看看有没有新微博发布  
测试的时候这样比较方便 要是拿来用的话可以酌情增加间隔时间  

![素材](http://i1.ciimg.com/602361/7bcbe6e02e0171d7.png)当有微博发布的时候  
![Markdown](http://i2.tiimg.com/602361/ee6b842aed3efef8.png)
![Markdown](http://i2.tiimg.com/602361/84396f4e9b8dc7c0.png)
![素材](http://i1.ciimg.com/602361/7bcbe6e02e0171d7.png)大功告成啦 监控小姐姐的微博去喽~  


>本文作者:奶权#米斯特安全团队 转载请注明出处
