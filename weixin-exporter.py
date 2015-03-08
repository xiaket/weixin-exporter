#!/usr/bin/env python
#coding=utf-8
"""
Author:         Xia Kai <xiaket@corp.netease.com/xiaket@gmail.com>
Filename:       weixin-exporter.py
Date created:   2013-08-07 19:50
Last modified:  2015-03-08 19:22
Modified by:    Xia Kai <xiaket@corp.netease.com/xiaket@gmail.com>

Description:

Changelog:
清理掉一些东西, 更新到现在的版本, 能把消息打印出来先.
"""
import commands
import os
import re
import sqlite3
import sys

from collections import defaultdict
from datetime import datetime


# 用iFunbox把微信的聊天记录复制到电脑.
WX_DATA_DIR = os.path.expanduser('~/.weixin/Documents')
# 解ipa文件, 把这个app复制出来.
WX_APP_DIR = os.path.expanduser('~/.weixin/MicroMessenger.app')
EMOTICON_RE = re.compile(r"(?P<name>\[.*?\])")
ID_RE = re.compile(r"[0-9A-Fa-f]{32}")
SESSION = "bf335f0598e916b3cfc710f813bc6b9c"


class Message(object):
    """ 一条微信消息. """
    def __init__(self, root_dir, session_id, data):
        self.root_dir = root_dir
        self.session_id = session_id
        self.pk = data[0]
        self.time = datetime.fromtimestamp(data[1])
        self.content = data[2]
        self.kind = data[4]
        self.sending = (data[5] == 0)
        self.data = data
        self.media_path = None
        self.received = self.data[5] == 1

    def format_appmsg(self):
        self.content = "[AppMsg]"

    def format_location(self):
        self.content = "[GeoLocation]"

    def format_videomsg(self):
        self.content = "[Video]"

    def format_voipmsg(self):
        self.content = "[VOIPMsg]"

    def format_voicemsg(self):
        """处理声音文件, 写明长度."""
        voicemsg_path = "%s/Audio/%s/%s.aud" % (
            self.root_dir, self.session_id, self.pk
        )
        if not os.path.isfile(voicemsg_path):
            self.content = "Voice Message of Unknown length"
            return

        fobj = open(voicemsg_path, 'rb')
        content = fobj.read()
        fobj.close()

        fobj = open("/tmp/wx.amr", "wb")
        fobj.write("#!AMR\n")
        fobj.write(content)
        fobj.close()
        cmd = "mplayer -vo null -ao null -frames 0 -identify /tmp/wx.amr 2>/dev/null | grep ID_LENGTH | awk -F '=' '{print $2}'"
        self.content = "[Voice Message. Length = %ss]" % commands.getoutput(cmd)

    def format_img(self):
        """返回图片文件路径."""
        self.content = "[Picture]"

    def format_emoji(self):
        self.content = "[Emoji]"

    def replace_media(self):
        """替换消息中的表情/图片/声音."""
        if self.kind == 10000:
            self.content = ""
        elif self.kind == 49:
            self.format_appmsg()
        elif self.kind == 48:
            self.format_location()
        elif self.kind == 47:
            self.format_emoji()
        elif self.kind == 34:
            self.format_voicemsg()
        elif self.kind in [43, 62]:
            self.format_videomsg()
        elif self.kind == 50:
            self.format_voipmsg()
        elif self.kind == 3:
            self.format_img()
        elif self.kind == 42:
            # I don't know what is this.
            pass
        elif self.kind != 1:
            sys.stderr.write(self.content + "\n")

    def __repr__(self):
        return "<%s: %s>" % (
            self.time.strftime("%Y-%m-%d"), self.content[:10].encode("UTF8")
        )


def find_target_dir():
    """
    我的Document下有三个目录, 一个是系统默认带的, id是32个0;
    一个是我曾经用qq登录微信(后来没用);
    一个是用微信号登录的, 是我常用的帐号.

    可能有用户会和我一样有多个目录, 这个函数负责找出
    惯常使用的用户目录(数据最多的目录), 并返回其路径.
    """
    names = [name for name in os.listdir(WX_DATA_DIR) if ID_RE.match(name)]
    dirs = {}
    for name in names:
        dir_path = os.path.normpath("%s/%s" % (WX_DATA_DIR, name))
        cmd = "du -s %s" % dir_path
        disk_size = int(commands.getoutput(cmd).split()[0])
        dirs[disk_size] = dir_path
    return dirs[max(dirs)]

def read_sessions(root_dir):
    """
    我这儿常年存了两个session, 一个是目标对象的聊天记录(舍不得删),
    一个是给自己的语音. 用来记录杂碎事情.
    """
    main_db = "%s/DB/MM.sqlite" % root_dir
    connection = sqlite3.connect(main_db)
    cursor = connection.cursor()
    sql = "SELECT MesLocalID,CreateTime,Message,ImgStatus,Type,Des from Chat_%s;" % SESSION
    cursor.execute(sql)
    return [Message(root_dir, SESSION, data) for data in cursor.fetchall()]

def main():
    target_dir_path = find_target_dir()
    messages = read_sessions(target_dir_path)
    dates = defaultdict(list)
    for message in messages:
        message.replace_media()
        dates[message.time.strftime("%y-%m-%d")].append(message)

    fobj = open("chatlog.txt", 'w')
    dates_list = dates.keys()
    dates_list.sort()
    for date in dates_list:
        fobj.write("### %s\n" % date)
        messages = dates[date]
        messages.sort(cmp=lambda x, y: cmp(x.time, y.time))
        for message in messages:
            if not message.content:
                continue
            if message.received:
                fobj.write("[Received]%s: %s\n" % (message.time.strftime("%H:%M"), message.content.encode("UTF-8")))
            else:
                fobj.write("[Sending]%s: %s\n" % (message.time.strftime("%H:%M"), message.content.encode("UTF-8")))
        fobj.write("\n")
    fobj.close()


if __name__ == '__main__':
    main()
