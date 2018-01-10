# -*- coding: UTF-8 -*-

import os, sys, time, logging, traceback, datetime
import jfSocket as jskt
import threading as td, socket

class TcpServer(object):
    """以 TCP 為連線基礎的 Socket Server  
    `host` : `tuple(ip, Port)` - 提供連線的 IPv4 位址與通訊埠號
    """
    def __init__(self, host):
        assert isinstance(host, tuple) and isinstance(host[0], str) and isinstance(host[1], int),\
            'host must be tuple(str, int) type!!'
        self.__host = host
        self.__acceptHandler = None
        self.__events = {
            jskt.EventTypes.STARTED : None,
            jskt.EventTypes.STOPED : None,
            jskt.EventTypes.CONNECTED : None,
            jskt.EventTypes.DISCONNECT : None,
            jskt.EventTypes.RECEIVED : None,
            jskt.EventTypes.SENDED : None,
            jskt.EventTypes.SENDFAIL : None
        }
        self.__stop = False
        self.__clients = {}
        self.__name = '{}:{}'.format(*(host))
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #Public Properties
    @property
    def host(self):
        """回傳本端提供連線的通訊埠號  
        回傳: 
        `tuple(ip, port)`
        """
        return self.__host
    @property
    def isAlive(self):
        """取得伺服器是否處於等待連線中  
        回傳: 
        `True` / `False`  
            *True* : 等待連線中  
            *False* : 停止等待
        """
        return self.__acceptHandler is not None and self.__acceptHandler.isAlive()
    @property
    def clients(self):
        """傳回已連接的連線資訊  
        回傳:
            `dictionary{ tuple(ip, port) : <TcpClient>, ... }`
        """
        return self.__clients.copy()
    # Public Methods
    def start(self):
        """啟動 TcpServer 伺服器，開始等待遠端連線          
        引發錯誤:   
            `Exception` -- 回呼的錯誤函式
        """
        try:
            self.__socket.bind(self.__host)
        except socket.error as ex:
            if ex.errno == 48:
                raise jskt.SocketError(1005)
            else:
                raise ex
        self.__socket.listen(5)
        self.__acceptHandler = td.Thread(target=self.__accept_client)
        self.__acceptHandler.setDaemon(True)
        self.__acceptHandler.start()
        now = time.time()
        while not self.__acceptHandler.isAlive and (time.time() - now) <= 1:
            time.sleep(0.1)
        if self.isAlive and self.__events[jskt.EventTypes.STARTED] is not None:
            try:
                self.__events[jskt.EventTypes.STARTED](self)
            except Exception as ex:
                raise ex
    def stop(self):
        """停止等待遠端連線
        """
        self.__stop = True
        self.close()
        self.__socket.close()
        self.__socket = None
        if self.__acceptHandler is not None:
            self.__acceptHandler.join(1.5)
    def bind(self, key=None, evt=None):
        """綁定回呼(callback)函式  
        具名參數:  
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
    def send(self, data, remote=None):
        """發送資料至遠端  
        傳入參數:  
            `data` `str` -- 欲傳送到遠端的資料  
        具名參數:  
            `remote` `tuple(ip, port)` -- 欲傳送的遠端連線；未傳入時，則發送給所有連線  
        引發錯誤:  
            `KeyError` -- 遠端連線不存在  
            `TypeError` -- 遠端連線不存在  
            `jfSocket.SocketError` -- 遠端連線已斷開  
            `Exception` -- 其他錯誤
        """
        if remote is not None:
            if not self.__clients.has_key(remote):
                raise KeyError()
            elif self.__clients[remote] is None:
                raise TypeError()
            elif not self.__clients[remote].isAlive:
                raise jskt.SocketError(1001)
            self.__clients[remote].send(data)
        else:
            for x in self.__clients:
                if self.__clients[x] is not None:
                    try:
                        self.__clients[x].send(data)
                    except Exception as ex:
                        raise ex
                else:
                    del self.__clients[x]
    def close(self, remote=None):
        """關閉遠端連線  
        具名參數:  
            `remote` `tuple(ip, port)` -- 欲關閉的遠端連線；未傳入時，則關閉所有連線  
        """
        if remote is not None:
            if not self.__clients.has_key(remote):
                return
            elif self.__clients[remote] is None or not self.__clients[remote].isAlive:
                del self.__clients[remote]
            else:
                self.__clients[remote].close()
        else:
            for x in self.__clients:
                if self.__clients[x] is not None:
                    self.__clients[x].close()
                else:
                    del self.__clients[x]

    #Private Methods
    def __onClientDisconnect(self, *args):
        client = args[0]
        if self.__clients[args[2]]:
            del self.__clients[args[2]]
        if self.__events[jskt.EventTypes.DISCONNECT] is not None:
            try:
                self.__events[jskt.EventTypes.DISCONNECT](*(args))
            except Exception as ex:
                print(traceback.format_exc())
                #raise ex
    def __accept_client(self):
        # 使用非阻塞方式等待連線，逾時時間為 1 秒
        self.__socket.settimeout(1)
        while not self.__stop:
            try:
                client, addr = self.__socket.accept()
            except socket.timeout:
                # 等待連線逾時，再重新等待
                continue
            except:
                # except (socket.error, IOError) as ex:
                # 先攔截並顯示，待未來確定可能會發生的錯誤再進行處理
                print(traceback.format_exc())
                break
            if self.__stop:
                try:
                    client.close()
                except:
                    pass
                break
            clk = jskt.TcpClient.TcpClient(client)
            clk.bind(key=jskt.EventTypes.RECEIVED, evt=self.__events[jskt.EventTypes.RECEIVED])
            clk.bind(key=jskt.EventTypes.DISCONNECT, evt=self.__onClientDisconnect)
            clk.bind(key=jskt.EventTypes.SENDED, evt=self.__events[jskt.EventTypes.SENDED])
            clk.bind(key=jskt.EventTypes.SENDFAIL, evt=self.__events[jskt.EventTypes.SENDFAIL])
            self.__clients[addr] = clk
            if self.__events[jskt.EventTypes.CONNECTED] is not None:
                try:
                    self.__events[jskt.EventTypes.CONNECTED](clk, self.__host, addr)
                except Exception as ex:
                    raise ex
        if self.__events[jskt.EventTypes.STOPED] is not None:
            try:
                self.__events[jskt.EventTypes.STOPED](self)
            except Exception as ex:
                raise ex
            

