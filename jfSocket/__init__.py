# -*- coding: UTF-8 -*-

#########################################
# Custom Socket Server and Client
# Author : Jaofeng Chen
#########################################

from enum import Enum, unique

class EventTypes(Enum):
    """事件代碼列舉
    
    提供 SckServer 與 SckClient 回呼用事件的鍵值
    """
    # Common Event
    CONNECTED = 'onConnected'
    DISCONNECT = 'onDisconnect'
    RECEIVED = 'onReceived'
    SENDED = 'onSended'
    SENDFAIL = 'onSendFail'
    # For SckServer Only
    SERVER_STARTED = 'onStarted'
    SERVER_STOPED = 'onStoped'

class TcpSocketError(Exception):
    pass

