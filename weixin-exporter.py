#!/usr/bin/env python
#coding=utf-8
"""
Author:         Xia Kai <xiaket@corp.netease.com/xiaket@gmail.com>
Filename:       weixin-exporter.py
Date created:   2013-08-07 19:50
Last modified:  2013-08-08 13:05

Description:

待实现特性列表:
    1. 能够更智能地找到session(综合用户和session)
    2. 找历史天气.
"""
import os
import re
import subprocess
import sqlite3

from datetime import datetime


WX_DATA_DIR = os.path.expanduser('~/.weixin/Documents')
WX_APP_DIR = os.path.expanduser('~/.weixin/MicroMessenger.app')
WX_EMOTICON_DICT = {
    '玫瑰': 64,
    '鼓掌': 43,
    '握手': 82,
    '呲牙': 14,
    '发呆': 4,
    '委屈': 50,
    '得意': 5,
    '难过': 16,
    '奋斗': 31,
    '糗大了': 44,
    '猪头': 63,
    '哈欠': 48,
    '拥抱': 79,
    '爱情': 91,
    '爱心': 67,
    '白眼': 23,
    'OK': 90,
    '可怜': 55,
    '流汗': 28,
    '疯了': 36,
    '左哼哼': 46,
    '偷笑': 21,
    '亲亲': 53,
    '大哭': 10,
    '快哭了': 51,
    '月亮': 76,
    '敲打': 39,
    '傲慢': 24,
    '悠闲': 30,
    '愉快': 22,
    '冷汗': 18,
    '抠鼻': 42,
    '蛋糕': 69,
    '吐': 20,
    '阴险': 52,
    '睡': 9,
    '擦汗': 41,
    '尴尬': 11,
    '调皮': 13,
    '晕': 35,
    '疑问': 33,
    '抓狂': 36,
    '流泪': 6,
    '闭嘴': 8,
    '惊恐': 27,
    '西瓜': 57,
    '微笑': 1,
    '嘘': 34,
    '强': 80,
    '勾引': 85,
    '酷': 17,
    '惊讶': 15,
    '困': 26,
    '右哼哼': 47,
    '害羞': 7,
    '色': 3,
    '坏笑': 45,
    '撇嘴': 2,
    '骷髅': 38,
    '衰': 37,
}
EMOTICON_RE = re.compile(r"(?P<name>\[.*?\])")
ID_RE = re.compile(r"[0-9A-Fa-f]{32}")


class Message(object):
    def __init__(self, _tuple):
        self.pk = _tuple[0]
        self.time = datetime.fromtimestamp(_tuple[1])
        self.content = _tuple[2]
        self.kind = _tuple[4]
        self.sending = (_tuple[5] == 0)

    def format_emoticon(self, name):
        """目前返回图片路径."""
        name = ''.join(name.groups()).strip("[]").encode("UTF8")
        emoticon_path = "%s/Expression_%s@2x.png" % (
            WX_APP_DIR, WX_EMOTICON_DICT[name],
        )
        return "<file://%s>" % emoticon_path

    def format_appmsg(self):
        print "format app msg"

    def format_location(self):
        print "format app msg"

    def format_voicemsg(self):
        print "format voice msg"

    def format_img(self):
        print "format img"

    def format_emoji(self):
        print "format emoji"

    def replace_media(self):
        """替换消息中的表情/图片/声音."""
        if self.kind == 10000:
            self.content = None
        elif self.kind == 49:
            self.format_appmsg()
        elif self.kind == 48:
            self.format_location()
        elif self.kind == 47:
            self.format_emoji()
        elif self.kind == 34:
            self.format_voicemsg()
        elif self.kind == 3:
            self.format_img()
        elif self.kind == 1 and re.findall(EMOTICON_RE, self.content):
            # 替换表情
            self.content = re.sub(
                EMOTICON_RE, self.format_emoticon, self.content,
            )
        elif self.kind != 1:
            print self.kind, self.content

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
        disk_size = int(subprocess.check_output(cmd.split()).split()[0])
        dirs[disk_size] = dir_path
    return dirs[max(dirs)]

def read_sessions(root_dir):
    """
    我这儿常年存了两个session, 一个是目标对象的聊天记录(舍不得删),
    一个是给自己的语音. 用来记录杂碎事情.
    """
    session_file = "%s/session/session.db" % root_dir
    connection = sqlite3.connect(session_file)
    cursor = connection.cursor()
    cursor.execute("select ConStrRes1 from SessionAbstract;")
    # 找到session的id, 这儿session存放时分了目录, 要拼起来.
    names = [''.join(_tup[0].split("/")[-2:]) for _tup in cursor.fetchall()]
    connection.close()

    sessions = {}
    # 找到sessionid的目的是在MM.sqlite中能够找到这个session的聊天记录.
    main_db = "%s/DB/MM.sqlite" % root_dir
    connection = sqlite3.connect(main_db)
    cursor = connection.cursor()
    for name in names:
        sql = "SELECT COALESCE(MAX(MesLocalID)+1, 0) from Chat_%s;" % name
        cursor.execute(sql)
        sessions[cursor.fetchone()[0]] = name
    # 拿到聊天记录最多的session.
    session_id = sessions[max(sessions)]
    sql = "SELECT MesLocalID,CreateTime,Message,ImgStatus,Type,Des from Chat_%s;" % session_id
    cursor.execute(sql)
    return [Message(_tuple) for _tuple in cursor.fetchall()]

def main():
    target_dir_path = find_target_dir()
    messages = read_sessions(target_dir_path)
    for message in messages:
        message.replace_media()

if __name__ == '__main__':
    main()
