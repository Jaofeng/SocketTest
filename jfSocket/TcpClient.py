# -*- coding: UTF-8 -*-

import os, sys, time, logging, traceback, datetime
import jfSocket as jskt
import threading as td, socket

class TcpClient(object):
    """用於定義可回呼的 TCP 連線型態的 Socket Client
    具名參數:  
        `socket` `socket` -- 承接的 Socket 類別，預設為 `None`  
        `evts` `dict{str:def,...}` -- 回呼事件定義，預設為 `None`
    """
    def __init__(self, socket=None, evts=None):
        self.__events = {
            jskt.EventTypes.CONNECTED : None,
            jskt.EventTypes.DISCONNECT : None,
            jskt.EventTypes.RECEIVED : None,
            jskt.EventTypes.SENDED : None,
            jskt.EventTypes.SENDFAIL : None
        }
        if evts:
            for x in evts:
                self.__events[x] = evts[x]
        self.socket = None
        self.__handler = None
        self.__host = None
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
    def connect(self, ip, port):
        """連線至遠端伺服器  
        傳入參數:  
            `ip` `str` - 遠端伺服器連線位址  
            `port` `int` - 遠端伺服器的通訊埠號  
        引發錯誤:  
            `TcpSocketError` -- 已有承接的 socket
            `socket.error' -- 連線時引發的錯誤
            `Exception` -- 回呼的錯誤函式
        """
        if self.socket is not None:
            raise jskt.TcpSocketError()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((ip, int(port)))
        except socket.error as err:
            raise err
        else:
            self.__assign(self.socket)
            if self.__events[jskt.EventTypes.CONNECTED] is not None:
                try:
                    self.__events[jskt.EventTypes.CONNECTED](self, self.host, self.remote)
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
        """關閉與遠端伺服器的連線"""
        if self.socket is not None:
            self.socket.close()
        self.socket = None
        if self.__handler is None:
            self.__handler.join(0.2)
        self.__handler = None
    def send(self, data):
        """發送資料至遠端伺服器  
        傳入參數:  
            `data` `str` -- 欲傳送到遠端的資料  
        引發錯誤:  
            `TcpSocketError` -- 遠端連線已斷開  
            `Exception` -- 回呼的錯誤函式
        """
        if not self.isAlive:
            raise jskt.TcpSocketError()
        try:
            self.socket.send(data)
        except Exception as e:
            if self.__events[jskt.EventTypes.SENDFAIL] is not None:
                try:
                    self.__events[jskt.EventTypes.SENDFAIL](self, data, e)
                except Exception as ex:
                    raise ex
        else:
            if self.__events[jskt.EventTypes.SENDED] is not None:
                try:
                    self.__events[jskt.EventTypes.SENDED](self, data)
                except Exception as ex:
                    raise ex
        
    # Private Methods
    def __assign(self, socket):
        self.socket = socket
        self.__host = socket.getsockname()
        self.__remote = socket.getpeername()
        self.__handler = td.Thread(target=self.__receiverHandler, args=(socket,))
        self.__handler.start()
    def __receiverHandler(self, client):
        client.settimeout(2)
        while 1:
            try:
                data = client.recv(self.recvBuffer)
            except socket.timeout:
                continue
            except socket.error as ex:
                break
            except:
                # print(traceback.format_exc())
                break
            if not data: 
                # Remote Disconnect
                break
            else:
                # Received Data
                if len(data) == 0:
                    # print('[**] Data length = 0')
                    break
                elif len([x for x in data if ord(x) == 0x04]) == len(data):
                    # print('[**] Client terminated:({}){}'.format(len(data), data.encode('hex')))
                    break
                if self.__events[jskt.EventTypes.RECEIVED] is not None:
                    try:
                        self.__events[jskt.EventTypes.RECEIVED](self, data)
                    except Exception as ex:
                        raise ex
        if self.__events[jskt.EventTypes.DISCONNECT] is not None:
            try:
                self.__events[jskt.EventTypes.DISCONNECT](self, self.host, self.remote)
            except Exception as ex:
                # print(traceback.format_exc())
                raise ex

