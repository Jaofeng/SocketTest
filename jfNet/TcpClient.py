#! /usr/bin/env python3
# # -*- coding: UTF-8 -*-

import os, sys, time, logging, traceback, datetime
from jfNet import *
import threading as td, socket

class TcpClient(object):
    """用於定義可回呼的 TCP 連線型態的 Socket Client
    具名參數:  
        `socket` `socket` -- 承接的 Socket 類別，預設為 `None`  
        `evts` `dict{str:def,...}` -- 回呼事件定義，預設為 `None`
    """
    def __init__(self, socket=None, evts=None):
        self.__events = {
            EventTypes.CONNECTED : None,
            EventTypes.DISCONNECT : None,
            EventTypes.RECEIVED : None,
            EventTypes.SENDED : None,
            EventTypes.SENDFAIL : None
        }
        if evts:
            for x in evts:
                self.__events[x] = evts[x]
        self.socket = None
        self.__handler = None
        self.__host = None
        self.__stop = False
        self.__remote = None
        self.recvBuffer = 256
        if socket is not None:
            self.__assign(socket)

    # Public Properties
    @property
    def isAlive(self):
        """取得目前是否正處於連線中  
        回傳: 
        `True` / `False`  
            *True* : 連線中  
            *False* : 連線已斷開
        """
        return self.__handler is not None and self.__handler.isAlive()
    @property
    def host(self):
        """回傳本端的通訊埠號  
        回傳: 
        `tuple(ip, port)`
        """
        return self.__host
    @property
    def remote(self):
        """回傳遠端伺服器的通訊埠號  
        回傳: 
        `tuple(ip, port)`
        """
        return self.__remote

    # Public Methods
    def connect(self, host):
        """連線至遠端伺服器  
        傳入參數:  
            `host` `tuple(ip, port)` - 遠端伺服器連線位址與通訊埠號  
        引發錯誤:  
            `jfSocket.SocketError` -- 連線已存在
            `socket.error' -- 連線時引發的錯誤
            `Exception` -- 回呼的錯誤函式
        """
        assert isinstance(host, tuple) and isinstance(host[0], str) and isinstance(host[1], int),\
            'host must be tuple(str, int) type!!'
        if self.isAlive:
            raise jskt.SocketError(1000)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect(host)
        except socket.error as err:
            raise err
        else:
            self.__assign(self.socket)
            if self.__events[EventTypes.CONNECTED] is not None:
                try:
                    self.__events[EventTypes.CONNECTED](self, self.host, self.remote)
                except Exception as ex:
                    raise ex              
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
    def close(self):
        """關閉與遠端伺服器的連線"""
        self.__stop = True
        if self.socket is not None:
            self.socket.close()
        self.socket = None
        if self.__handler is None:
            self.__handler.join(2.5)
        self.__handler = None
    def send(self, data):
        """發送資料至遠端伺服器  
        傳入參數:  
            `data` `str` -- 欲傳送到遠端的資料  
        引發錯誤:  
            `jfSocket.SocketError` -- 遠端連線已斷開  
            `Exception` -- 回呼的錯誤函式
        """
        if not self.isAlive:
            raise jskt.SocketError(1001)
        try:
            self.socket.send(data)
        except Exception as e:
            if self.__events[EventTypes.SENDFAIL] is not None:
                try:
                    self.__events[EventTypes.SENDFAIL](self, data, e)
                except Exception as ex:
                    raise ex
        else:
            if self.__events[EventTypes.SENDED] is not None:
                try:
                    self.__events[EventTypes.SENDED](self, data)
                except Exception as ex:
                    raise ex
        
    # Private Methods
    def __assign(self, socket):
        self.socket = socket
        self.__host = socket.getsockname()
        self.__remote = socket.getpeername()
        self.__handler = td.Thread(target=self.__receiverHandler, args=(socket,))
        self.__stop = False
        self.__handler.start()
    def __receiverHandler(self, client):
        # 使用非阻塞方式等待資料，逾時時間為 2 秒
        client.settimeout(2)
        while not self.__stop:
            try:
                data = client.recv(self.recvBuffer)
            except socket.timeout:
                # 等待資料逾時，再重新等待
                if self.__stop:
                    break
                else:
                    continue
            except:
                # 先攔截並顯示，待未來確定可能會發生的錯誤再進行處理
                print(traceback.format_exc())
                break
            if not data: 
                # 空資料，認定遠端已斷線
                break
            else:
                # Received Data
                if len(data) == 0:
                    # 空資料，認定遠端已斷線
                    break
                elif len([x for x in data if ord(x) == 0x04]) == len(data):
                    # 收到 EOT(End Of Transmission, 傳輸結束)，則表示已與遠端中斷連線
                    break
                if self.__events[EventTypes.RECEIVED] is not None:
                    try:
                        self.__events[EventTypes.RECEIVED](self, data)
                    except Exception as ex:
                        raise
        if self.__events[EventTypes.DISCONNECT] is not None:
            try:
                self.__events[EventTypes.DISCONNECT](self, self.host, self.remote)
            except Exception as ex:
                raise

