#! /usr/bin/env python3
# # -*- coding: UTF-8 -*-

import os, sys, time, logging, traceback, datetime
import threading as td, socket
from jfSocket.Common import *

class CastSender(object):
    """建立一個發送 Multicast 多播的連線類別
    傳入參數:  
        `evts` `dict{str:def,...}` -- 回呼事件定義，預設為 `None`
    """
    def __init__(self, evts=None):
        self.__events = {
            EventTypes.SENDED : None,
            EventTypes.SENDFAIL : None
        }
        if evts:
            for x in evts:
                self.__events[x] = evts[x]
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.INADDR_ANY)	

    def bind(self, key=None, evt=None):
        """綁定回呼(callback)函式  
        傳入參數:  
            `key` `str` -- 回呼事件代碼；為避免錯誤，建議使用 *EventTypes* 列舉值  
            `evt` `def` -- 回呼(callback)函式  
        引發錯誤:  
            `KeyError` -- 回呼事件代碼錯誤  
            `TypeError` -- 型別錯誤，必須為可呼叫執行的函式
        """
        if key not in self.__events:
            raise KeyError('key:\'{}\' not found!'.format(key))
        if evt is not None and not callable(evt):
            raise TypeError('evt:\'{}\' is not a function!'.format(evt))
        self.__events[key] = evt
        
    def send(self, remote, data):
        """發送資料至多播位址  
        傳入參數:  
            `remote` `tuple(ip, port)` -- 多播位址
            `data` `str` -- 欲傳送的資料  
        引發錯誤:  
            `jfSocket.SocketError` -- 遠端連線已斷開  
            `Exception` -- 回呼的錯誤函式
        """
        v = socket.inet_aton(remote[0])[0]
        if isinstance(v, str):
            v = ord(v)
        if v not in range(224, 240):
            raise SocketError(1004)
        data = data.encode('utf-8')
        ba = bytearray(data)
        try:
            self.__socket.sendto(ba, (remote[0], int(remote[1])))
        except Exception as e:
            if self.__events[EventTypes.SENDFAIL] is not None:
                try:
                    self.__events[EventTypes.SENDFAIL](self, ba, remote, e)
                except Exception as ex:
                    raise ex
        else:
            if self.__events[EventTypes.SENDED] is not None:
                try:
                    self.__events[EventTypes.SENDED](self, ba, remote)
                except Exception as ex:
                    raise ex
        
