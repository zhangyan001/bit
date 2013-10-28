# -*- coding:utf-8 -*-
# Create your views here.

from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import render_to_response,RequestContext
from django.contrib import messages
from models import ContentModel
import datetime
import urllib,urllib2,time,hashlib
import xml.etree.ElementTree as ET
from django.views.decorators.csrf import csrf_exempt  
import re
# from django.utils.encoding import smart_str, smart_unicode
import xiaoche
import translate
import huanyi
import weather
import renren
import news
import ferrybus
import freshman

TOKEN = "bit"

welcome_msg = u"""
欢迎关注「设计北理」公众平台
"""

help_info = u"""
「设计改变生活」

0.发送「新闻」或「体育」或「NBA」或「bbc world」或「bbc china」，查看相应新闻。
1.发送「校车」或「明天校车」可以查看今天或明天校车时刻表。
2.发送「摆渡车」可以查看良乡校区摆渡车时刻表。
3.发送「环一」或「环1」可以查看环1公交发车时刻。
4.发送「天气」或「空气」可以查看天气预报或当前空气质量。
5.发送英文单词或句子可以进行翻译。

如果想跟我说话，请在开头加上「#」。你不会收到自动回复，但我会在后台看到。

每周发布数学作业参考答案及解答过程，请推荐，谢谢～
"""

report_info = u"""
报告bug或有任何建议请发邮件至lion2@vip.qq.com
©zhang
"""

# news_info = u"""输入「网易新闻」或者「谷歌新闻」或者「bbc world」或者「bbc china」即可查看新闻。"""

@csrf_exempt
def handleRequest(request):
        if request.method == 'GET':
                response = HttpResponse(checkSignature(request),content_type="text/plain")
                return response
        elif request.method == 'POST':
                response = HttpResponse(responseMsg(request),content_type="application/xml")
                return response
        else:
                return None

def checkSignature(request):
        global TOKEN
        signature = request.GET.get("signature", None)
        timestamp = request.GET.get("timestamp", None)
        nonce = request.GET.get("nonce", None)
        echoStr = request.GET.get("echostr",None)

        token = TOKEN
        tmpList = [token,timestamp,nonce]
        tmpList.sort()
        tmpstr = "%s%s%s" % tuple(tmpList)
        tmpstr = hashlib.sha1(tmpstr).hexdigest()
        if tmpstr == signature:
                return echoStr
        else:
                return None

def responseMsg(request):
    # post_data = smart_str(request.raw_post_data)
    post_data = request.raw_post_data
    msg = paraseMsgXml(post_data)
    if msg['MsgType'] == "text":
        content, contentType = process(msg['Content'])
    elif msg['MsgType'] == "event" and msg['Event'] == 'subscribe':
        content, contentType = subscribe()
    else:
        content = u"sorry, 我暂时只有以下功能：" + help_info
        contentType = "text"
    return replyXml(msg, content, contentType)
    
def subscribe():
    return welcome_msg+help_info, "text"
    
def process(msg):
    if msg.startswith('#') or msg.startswith('＃'):
       pass
    elif msg == u'新生指南':
        return freshman.get_guidance(), "news"
    elif msg == u'新闻' or msg == u'体育' or msg == u'体育新闻':
        return news.getNews(msg), "news"
    elif isinstance(msg, type('string')):
        msg = msg.lower()
        msg = msg.strip()
        if msg == 'bbc world' or msg == 'bbc china' or msg == 'bbc' or msg == 'nba':
            return news.getNews(msg), "news"
        else:
            return translate.translate(msg), "text"
    #elif msg == u'新闻':
    #    return news_info, "text"
    elif msg == u'校车' or msg == u'明天校车':
        return xiaoche.get_timetable(msg), "text"
    elif msg == u'摆渡车':
        return ferrybus.get_timetable(msg), "text"
    elif msg == u'环一' or msg == u'环1':
        return huanyi.get_timetable(), "text"
    elif msg == u'天气':
        return weather.weather(), "text"
    elif msg == u'空气':
        return weather.get_airquality(), "text"
    elif re.match(u"发状态", msg):
        if msg[3:]:
            return renren.renren_status(msg[3:]), "text"
        else:
            return u"请输入状态内容", "text"
    else:
        return u"无法处理请求，请查看使用说明\n" + help_info + report_info, "text"

def paraseMsgXml(raw_msg):  
    root = ET.fromstring(raw_msg)
    msg = {} 
    if root.tag == 'xml':  
        for child in root:
            msg[child.tag] = (child.text)
    return msg

def replyXml(recvmsg, replyContent, contentType):
    textTpl = """ <xml>
                <ToUserName><![CDATA[%s]]></ToUserName>
                <FromUserName><![CDATA[%s]]></FromUserName> 
                <CreateTime>%s</CreateTime>
                <MsgType><![CDATA[%s]]></MsgType>
                <Content><![CDATA[%s]]></Content>
                <FuncFlag>0</FuncFlag>
                </xml>
                """

    newsTpl_head = """
                 <xml>
                 <ToUserName><![CDATA[%s]]></ToUserName>
                 <FromUserName><![CDATA[%s]]></FromUserName>
                 <CreateTime>%s</CreateTime>
                 <MsgType><![CDATA[news]]></MsgType>
                 <ArticleCount>%d</ArticleCount>
                 <Articles>
                    """
    newsTpl_item = """
                 <item>
                 <Title><![CDATA[%s]]></Title> 
                 <Description><![CDATA[%s]]></Description>
                 <PicUrl><![CDATA[%s]]></PicUrl>
                 <Url><![CDATA[%s]]></Url>
                 </item>
                 """

    newsTpl_tail = """
                </Articles>
                <FuncFlag>1</FuncFlag>
                </xml> 
                """

    if contentType == "text":
        echostr = textTpl % (recvmsg['FromUserName'], recvmsg['ToUserName'], recvmsg['CreateTime'], "text", replyContent)
    elif contentType == "news":
        echostr = newsTpl_head % (recvmsg['FromUserName'], recvmsg['ToUserName'], recvmsg['CreateTime'], replyContent[0])
        for item in replyContent[1]:
            echostr += newsTpl_item % (item[0], item[1], item[2], item[3])
        echostr += newsTpl_tail

    return echostr


def index(request):
    return render_to_response('index.html')

def about(request):
    return render_to_response('about.html')

def status(request):
    ipaddr = request.META.get('REMOTE_ADDR', '')
    if request.method == 'POST':
        _content = request.POST.get('content', '')
        if not checkIP(ipaddr):
            messages.error(request, 'IP_NOT_VALID')
        elif not (len(_content) < 120 and len(_content) > 1):
            messages.error(request, u'字数超出限制，请精简')
        elif ContentModel.objects.filter(ip=ipaddr, time__range=\
                (datetime.datetime.now() - datetime.timedelta(minutes=5), datetime.datetime.now())).count() > 0:
            messages.error(request, u'你刚刚发过，请稍后')
        else:
            new_content = ContentModel(ip=ipaddr, 
                    time=datetime.datetime.now())
            new_content.save()
            try:
                #postStatu(_content, ContentModel.objects.count())
                _content = _content + u"(发送自 http://bithelper.sinaapp.com/status/ )"
                renren.renren_status(_content)
            except RuntimeError:
                messages.error(request, u'出错了，请稍后再试')
                logging.error('Error in ' + str(ContentModel.objects.count()))
            else:
                messages.success(request, u'状态发送成功')
    return render_to_response('status.html', 
            context_instance=RequestContext(request))

def checkIP(ipaddr):
    return True
