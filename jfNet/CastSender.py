#! /usr/bin/env python3
# # -*- coding: UTF-8 -*-

import struct
import socket
from . import EventTypes


class CastSender:
    """建立一個發送 Multicast 多播的連線類別
    傳入參數:
        `host` `tuple(ip, port)` -- 綁定的通訊埠，預設為 `None`
    """
    _socket: socket.socket = None
    _events = {
        EventTypes.SENDED: None,
        EventTypes.SENDFAIL: None
    }
    _loopBack = False

    def __init__(self, host:tuple=None):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 32))
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1 if self._loopBack else 0)
        if host:
            self._socket.bind(host)

    def bind(self, key:EventTypes, evt=None):
        """綁定回呼(callback)函式
        傳入參數:
            `key` `str` -- 回呼事件代碼；為避免錯誤，建議使用 *EventTypes* 列舉值
            `evt` `def` -- 回呼(callback)函式
        引發錯誤:
            `KeyError` -- 回呼事件代碼錯誤
            `TypeError` -- 型別錯誤，必須為可呼叫執行的函式
        """
        if key not in self._events:
            raise KeyError('key:\'{}\' not found!'.format(key))
        if evt is not None and not callable(evt):
            raise TypeError('evt:\'{}\' is not a function!'.format(evt))
        self._events[key] = evt

    def send(self, remote:tuple, data):
        """發送資料至多播位址
        傳入參數:
            `remote` `tuple(ip, port)` -- 多播位址
            `data` `str or bytearray` -- 欲傳送的資料
        引發錯誤:
            `jfSocket.SocketError` -- 遠端連線已斷開
            `Exception` -- 回呼的錯誤函式
        """
        v = socket.inet_aton(remote[0])[0]
        if isinstance(v, str):
            v = ord(v)
        if v not in range(224, 240):
            raise SocketError(1004)
        ba = None
        if isinstance(data, str):
            data = data.encode('utf-8')
            ba = bytearray(data)
        elif isinstance(data, bytearray):
            ba = data[:]
        try:
            self._socket.sendto(ba, (remote[0], int(remote[1])))
        except Exception as e:
            if self._events[EventTypes.SENDFAIL]:
                self._events[EventTypes.SENDFAIL](self, ba, remote, e)
        else:
            if self._events[EventTypes.SENDED]:
                self._events[EventTypes.SENDED](self, ba, remote)
