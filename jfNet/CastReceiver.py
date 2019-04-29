#! /usr/bin/env python3
# # -*- coding: UTF-8 -*-

import time
import traceback
import errno
import struct
import threading
import socket
from . import EventTypes, SocketError


class CastReceiver:
    '''建立多播監聽器(Multicast)類別
    傳入參數:
        `port` `int` -- 欲監聽的通訊埠號
        `evts` `dict{str:def,...}` -- 回呼事件定義，預設為 `None`
    '''

    _socket:socket.socket = None
    _host:tuple = None
    _events:dict = {
        EventTypes.STARTED: None,
        EventTypes.STOPED: None,
        EventTypes.RECEIVED: None,
        EventTypes.JOINED_GROUP: None
    }
    _groups = []
    _stop = False
    _receiveHandler: threading.Thread = None
    _reuseAddr = True
    _reusePort = False
    recvBuffer = 256

    def __init__(self, host):
        if isinstance(host, int):
            self._host = ('', host)
        elif isinstance(host, tuple):
            self._host = host

    # Public Properties
    @property
    def groups(self) -> list:
        '''取得已註冊監聽的群組IP
        回傳: `list(str, ...)` -- 已註冊的IP
        '''
        return self._groups[:]

    @property
    def host(self) -> tuple:
        '''回傳本端的通訊埠號
        回傳: `tuple(ip, port)`
        '''
        return self._host

    @property
    def isAlive(self) -> bool:
        '''取得多播監聽器是否處於監聽中
        回傳: `boolean`
            *True* : 等待連線中
            *False* : 停止等待
        '''
        return self._receiveHandler and self._receiveHandler.is_alive()

    @property
    def reuseAddr(self) -> bool:
        '''取得是否可重複使用 IP 位置
        回傳: `boolean`
            *True* : 可重複使用
            *False* : 不可重複使用
        '''
        return self._reuseAddr

    @reuseAddr.setter
    def reuseAddr(self, value: bool):
        '''設定是否可重複使用 IP 位置
        '''
        if not isinstance(value, bool):
            raise TypeError()
        self._reuseAddr = value
        if self._socket:
            self._socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 if self._reuseAddr else 0
            )

    @property
    def reusePort(self) -> bool:
        '''取得是否可重複使用通訊埠位
        回傳: `boolean`
            *True* : 可重複使用
            *False* : 不可重複使用
        '''
        return self._reusePort

    @reusePort.setter
    def reusePort(self, value:bool):
        '''設定是否可重複使用通訊埠位
        '''
        if not isinstance(value, bool):
            raise TypeError()
        self._reusePort = value
        if self._socket:
            self._socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEPORT, 1 if self._reusePort else 0
            )

    # Public Methods
    def start(self):
        '''啟動多播監聽伺服器
        引發錯誤:
            `socket.error` -- 監聽 IP 設定錯誤
            `Exception` -- 回呼的錯誤函式
        '''
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 32))
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 if self._reuseAddr else 0)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1 if self._reusePort else 0)
        try:
            self._socket.bind(self._host)
        except socket.error as ex:
            if ex.errno == 48:
                raise SocketError(1005)
            else:
                raise ex
        self._receiveHandler = threading.Thread(target=self._receive_handler)
        self._receiveHandler.setDaemon(True)
        self._receiveHandler.start()
        now = time.time()
        while not self._receiveHandler.isAlive and (time.time() - now) <= 1:
            time.sleep(0.1)
        for x in self._groups:
            self._doAddMembership(x)
        if self.isAlive and self._events[EventTypes.STARTED]:
            self._events[EventTypes.STARTED](self)

    def stop(self):
        '''停止監聽
        '''
        self._stop = True
        if self._socket:
            for x in self._groups:
                self._doDropMembership(x)
            self._socket.close()
        self._socket = None
        if self._receiveHandler is not None:
            self._receiveHandler.join(2.5)
        self._receiveHandler = None

    def joinGroup(self, ips:list):
        '''加入監聽IP
        傳入參數:
            `ips` `list(str, ...)` -- 欲監聽的 IP 陣列 list
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
            if x in self._groups:
                raise SocketError(1002)
            self._groups.append(x)
            if self._socket:
                self._doAddMembership(x)

    def dropGroup(self, ips:list):
        '''移除監聽清單中的 IP
        `注意`：如在監聽中移除IP，需重新啟動
        傳入參數:
            `ips` `list(str, ...)` -- 欲移除監聽的 IP 陣列 list
        引發錯誤:
            `SocketError` -- 欲移除的 IP 錯誤或該 IP 不存在
        '''
        for x in ips:
            v = socket.inet_aton(x)[0]
            if isinstance(v, str):
                v = ord(v)
            if v not in range(224, 240):
                raise SocketError(1004)
            if x not in self._groups:
                raise SocketError(1003)
            self._groups.remove(x)
            if self._socket:
                self._doDropMembership(x)

    def bind(self, key:str=None, evt=None):
        '''綁定回呼(callback)函式
        傳入參數:
            `key` `str` -- 回呼事件代碼；為避免錯誤，建議使用 *EventTypes* 列舉值
            `evt` `def` -- 回呼(callback)函式
        引發錯誤:
            `KeyError` -- 回呼事件代碼錯誤
            `TypeError` -- 型別錯誤，必須為可呼叫執行的函式
        '''
        if key not in self._events:
            raise KeyError('key:"{}" not found!'.format(key))
        if evt is not None and not callable(evt):
            raise TypeError('evt:"{}" is not a function!'.format(evt))
        self._events[key] = evt

    # Private Methods
    def _receive_handler(self):
        # 使用非阻塞方式等待資料，逾時時間為 2 秒
        self._socket.settimeout(2)
        buff = bytearray(self.recvBuffer)
        while not self._stop:
            try:
                nbytes, addr = self._socket.recvfrom_into(buff)
                data = buff[:nbytes]
            except socket.timeout:
                # 等待資料逾時，再重新等待
                if self._stop:
                    break
                else:
                    continue
            except OSError:
                break
            except:
                # 先攔截並顯示，待未來確定可能會發生的錯誤再進行處理
                print(traceback.format_exc())
                break
            if not data:
                # 空資料，認定遠端已斷線
                break
            else:
                # Received Data
                if self._events[EventTypes.RECEIVED]:
                    self._events[EventTypes.RECEIVED](self, data, self._socket.getsockname(), addr)
        if self._events[EventTypes.STOPED]:
            self._events[EventTypes.STOPED](self)

    def _doAddMembership(self, ip):
        try:
            mreq = struct.pack('4sL', socket.inet_aton(ip), socket.INADDR_ANY)
            self._socket.setsockopt(
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
            if self._events[EventTypes.JOINED_GROUP]:
                self._events[EventTypes.JOINED_GROUP](self, ip)

    def _doDropMembership(self, ip):
        try:
            mreq = struct.pack('4sL', socket.inet_aton(ip), socket.INADDR_ANY)
            self._socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq
            )
        except socket.error as err:
            if err.errno == errno.EADDRNOTAVAIL:
                # print(' -> Not In Use')
                pass
            else:
                # print(' -> error({})'.format(err.errno))
                raise
