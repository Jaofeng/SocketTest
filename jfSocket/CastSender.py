# -*- coding: UTF-8 -*-

import os, sys, time, logging, traceback, datetime
import jfSocket as jskt
import threading as td, socket

class CastSender(object):
    def __init__(self, evts=None):
        self.__events = {
            jskt.EventTypes.SENDED : None,
            jskt.EventTypes.SENDFAIL : None
        }
        if evts:
            for x in evts:
                self.__events[x] = evts[x]
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
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
        if ord(socket.inet_aton(remote)[0]) not in range(224, 240):
            raise jskt.SocketError(1004)
        try:
            self.__socket.sendto(data, (remote[0], int(remote[1])))
        except Exception as e:
            if self.__events[jskt.EventTypes.SENDFAIL] is not None:
                try:
                    self.__events[jskt.EventTypes.SENDFAIL](self, data, remote, e)
                except Exception as ex:
                    raise ex
        else:
            if self.__events[jskt.EventTypes.SENDED] is not None:
                try:
                    self.__events[jskt.EventTypes.SENDED](self, data, remote)
                except Exception as ex:
                    raise ex
        
