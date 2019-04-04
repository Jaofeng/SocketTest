#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

from enum import Enum, unique

class EventTypes(Enum):
    """事件代碼列舉  
    提供 `jfSocket` 所有類別回呼用事件的鍵值
    """
    CONNECTED = 'onConnected'
    DISCONNECT = 'onDisconnect'
    RECEIVED = 'onReceived'
    SENDED = 'onSended'
    SENDFAIL = 'onSendFail'
    STARTED = 'onStarted'
    STOPED = 'onStoped'

class SocketError(Exception):
    """自訂錯誤類別  
    傳入參數:  
        `errno` `int` - 錯誤代碼  
    具名參數:  
        `err` `Exception` - 內部引發的錯誤  
    """
    def __init__(self, errno, err=None):
        self.errno = errno
        self.innererr = err
    def __str__(self):
        return '[ErrNo:{}] {}'.format(self.errno, self.message)
    @property
    def message(self):
        """錯誤說明文字  
        回傳: `str`
        """
        return errcode[self.errno]
