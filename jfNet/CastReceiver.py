#! /usr/bin/env python3
# # -*- coding: UTF-8 -*-

import sys, time, traceback, errno, struct
import threading as td, socket
from jfNet import *


class CastReceiver(object):
    '''建立多播監聽器(Multicast)類別  
    傳入參數:  
        `port` `int` -- 欲監聽的通訊埠號  
        `evts` `dict{str:def,...}` -- 回呼事件定義，預設為 `None`
    '''

    __socket = None

    def __init__(self, host, evts=None):
        if isinstance(host, int):
            self.__host = ('', host)
        elif isinstance(host, tuple):
            self.__host = host
        self.__receiveHandler = None
        self.__stop = False
        self.__groups = []
        self.__events = {
            EventTypes.STARTED: None,
            EventTypes.STOPED: None,
            EventTypes.RECEIVED: None,
        }
        if evts:
            for x in evts:
                self.__events[x] = evts[x]
        self.__reuseAddr = True
        self.__reusePort = True
        self.recvBuffer = 256

    # Public Properties
    @property
    def groups(self):
        '''取得已註冊監聽的群組IP  
        回傳: `list(str, ...)` -- 已註冊的IP
        '''
        return self.__groups[:]

    @property
    def host(self):
        '''回傳本端的通訊埠號  
        回傳: `tuple(ip, port)`
        '''
        return self.__host

    @property
    def isAlive(self):
        '''取得多播監聽器是否處於監聽中  
        回傳: `boolean`  
            *True* : 等待連線中  
            *False* : 停止等待
        '''
        return self.__receiveHandler is not None and self.__receiveHandler.isAlive()

    @property
    def reuseAddr(self):
        '''取得是否可重複使用 IP 位置  
        回傳: `boolean`  
            *True* : 可重複使用  
            *False* : 不可重複使用
        '''
        return self.__reuseAddr

    @reuseAddr.setter
    def reuseAddr(self, value):
        '''設定是否可重複使用 IP 位置  
        '''
        if not isinstance(value, bool):
            raise TypeError()
        self.__reuseAddr = value
        if self.__socket:
            self.__socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 if self.__reuseAddr else 0
            )

    @property
    def reusePort(self):
        '''取得是否可重複使用通訊埠位  
        回傳: `boolean`  
            *True* : 可重複使用  
            *False* : 不可重複使用
        '''
        return self.__reusePort

    @reusePort.setter
    def reusePort(self, value):
        '''設定是否可重複使用通訊埠位
        '''
        if not isinstance(value, bool):
            raise TypeError()
        self.__reusePort = value
        if self.__socket:
            self.__socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEPORT, 1 if self.__reusePort else 0
            )

    # Public Methods
    def start(self):
        '''啟動多播監聽伺服器  
        引發錯誤:  
            `socket.error` -- 監聽 IP 設定錯誤
            `Exception` -- 回呼的錯誤函式
        '''
        self.__socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self.__socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 if self.__reuseAddr else 0
        )
        self.__socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEPORT, 1 if self.__reusePort else 0
        )
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        for x in self.__groups:
            self.__doAddMembership(x)
        try:
            self.__socket.bind(self.__host)
        except socket.error as ex:
            if ex.errno == 48:
                raise SocketError(1005)
            else:
                raise ex
        self.__receiveHandler = td.Thread(
            target=self.__receive_handler, args=(self.__socket,)
        )
        self.__receiveHandler.setDaemon(True)
        self.__receiveHandler.start()
        now = time.time()
        while not self.__receiveHandler.isAlive and (time.time() - now) <= 1:
            time.sleep(0.1)
        if self.isAlive and self.__events[EventTypes.STARTED] is not None:
            try:
                self.__events[EventTypes.STARTED](self)
            except Exception as ex:
                raise

    def stop(self):
        '''停止監聽
        '''
        self.__stop = True
        if self.__socket:
            for x in self.__groups:
                self.__doDropMembership(x)
            self.__socket.close()
        self.__socket = None
        if self.__receiveHandler is not None:
            self.__receiveHandler.join(2.5)
        self.__receiveHandler = None

    def joinGroup(self, *ips):
        '''加入監聽IP  
        傳入參數:  
            `*ips` `list(str, ...)` -- 欲監聽的 IP 陣列 list  
        引發錯誤:  
            `SocketError` -- 監聽的 IP 錯誤或該 IP 已在監聽中
            `socket.error` -- 無法設定監聽 IP 
        '''
        for x in ips:
            v = socket.inet_aton(x)[0]
            if isinstance(v, str):
                v = ord(v)
            if v not in range(224, 240):
                raise SocketError(1004)
            if x in self.__groups:
                raise SocketError(1002)
            self.__groups.append(x)
            if self.__socket:
                self.__doAddMembership(x)

    def dropGroup(self, *ips):
        '''移除監聽清單中的 IP  
        `注意`：如在監聽中移除IP，需重新啟動
        傳入參數:  
            `*ips` `list(str, ...)` -- 欲移除監聽的 IP 陣列 list  
        引發錯誤:  
            `SocketError` -- 欲移除的 IP 錯誤或該 IP 不存在
        '''
        for x in ips:
            v = socket.inet_aton(x)[0]
            if isinstance(v, str):
                v = ord(v)
            if v not in range(224, 240):
                raise SocketError(1004)
            if x not in self.__groups:
                raise SocketError(1003)
            self.__groups.remove(x)
            if self.__socket:
                self.__doDropMembership(x)
                    
    def bind(self, key=None, evt=None):
        '''綁定回呼(callback)函式  
        傳入參數:  
            `key` `str` -- 回呼事件代碼；為避免錯誤，建議使用 *EventTypes* 列舉值  
            `evt` `def` -- 回呼(callback)函式  
        引發錯誤:  
            `KeyError` -- 回呼事件代碼錯誤  
            `TypeError` -- 型別錯誤，必須為可呼叫執行的函式
        '''
        if key not in self.__events:
            raise KeyError('key:"{}" not found!'.format(key))
        if evt is not None and not callable(evt):
            raise TypeError('evt:"{}" is not a function!'.format(evt))
        self.__events[key] = evt

    # Private Methods
    def __receive_handler(self, sock):
        # 使用非阻塞方式等待資料，逾時時間為 2 秒
        sock.settimeout(2)
        buff = bytearray(self.recvBuffer)
        while not self.__stop:
            try:
                nbytes, addr = sock.recvfrom_into(buff)
                data = buff[:nbytes]
            except socket.timeout:
                # 等待資料逾時，再重新等待
                if self.__stop:
                    break
                else:
                    continue
            except OSError:
                break
            except Exception as ex:
                # 先攔截並顯示，待未來確定可能會發生的錯誤再進行處理
                print(traceback.format_exc())
                break
            if not data:
                # 空資料，認定遠端已斷線
                break
            else:
                # Received Data
                # if len(data) == 0:
                #     # 空資料，認定遠端已斷線
                #     break
                # elif len([x for x in data if ord(x) == 0x04]) == len(data):
                #     # 收到 EOT(End Of Transmission, 傳輸結束)，則表示已與遠端中斷連線
                #     break
                if self.__events[EventTypes.RECEIVED] is not None:
                    try:
                        self.__events[EventTypes.RECEIVED](
                            self, data, sock.getsockname(), addr
                        )
                    except Exception as ex:
                        raise ex
        if self.__events[EventTypes.STOPED] is not None:
            try:
                self.__events[EventTypes.STOPED](self)
            except Exception as ex:
                raise ex

    def __doAddMembership(self, ip):
        try:
            mreq = struct.pack('4sL', socket.inet_aton(ip), socket.INADDR_ANY)
            self.__socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq
            )
        except socket.error as err:
            if err.errno == errno.EADDRINUSE:
                # print(' -> In Use')
                pass
            else:
                # print(' -> error({})'.format(err.errno))
                raise
        else:
            # print(' -> OK')
            pass

    def __doDropMembership(self, ip):
        try:
            mreq = struct.pack('4sL', socket.inet_aton(ip), socket.INADDR_ANY)
            self.__socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq
            )
        except socket.error as err:
            if err.errno == errno.EADDRNOTAVAIL:
                # print(' -> Not In Use')
                pass
            else:
                # print(' -> error({})'.format(err.errno))
                raise
        else:
            # print(' -> OK')
            pass
