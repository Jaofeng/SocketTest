#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

#########################################
# Custom Socket Server and Client
# Author : Jaofeng Chen
#########################################

# jfSocket.SocketError 錯誤代碼清單
errcode = {}
errcode[1000] = '連線已存在'
errcode[1001] = '遠端連線已斷開，或尚未連線'
errcode[1002] = '位址已存在'
errcode[1003] = '位址不存在'
errcode[1004] = '多播(Multicast)位址不正確，應為 224.0.0.0 ~ 239.255.255.255'
errcode[1005] = '[多播]此位址已在使用中，請使用 reuseAddr 與 reusePort'
