# -*- coding: UTF-8 -*-

#########################################
# Custom Socket Server and Client
# Author : Jaofeng Chen
#########################################

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

# jfSocket.SocketError 錯誤代碼清單
errcode = {}
errcode[1000] = '連線已存在'
errcode[1001] = '遠端連線已斷開，或尚未連線'
errcode[1002] = '位址已存在'
errcode[1003] = '位址不存在'
errcode[1004] = '多播(Multicast)位址不正確，應為 224.0.0.0 ~ 239.255.255.255'
errcode[1005] = '此位址已在使用中'
