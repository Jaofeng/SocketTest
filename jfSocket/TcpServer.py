# -*- coding: UTF-8 -*-

import os, sys, time, logging, traceback, datetime
import jfSocket as jskt
import threading as td, socket

class TcpServer(object):
    """遠端以連線之事件

    格式：function(client:socket)
    """
    def __init__(self, ip, port):
        self.__host = (ip, port)
        self.__acceptHandler = None
        self.__events = {
            jskt.EventTypes.SERVER_STARTED : None,
            jskt.EventTypes.SERVER_STOPED : None,
            jskt.EventTypes.CONNECTED : None,
            jskt.EventTypes.DISCONNECT : None,
            jskt.EventTypes.RECEIVED : None,
            jskt.EventTypes.SENDED : None,
            jskt.EventTypes.SENDFAIL : None
        }
        self.__stop = False
        self.__clients = {}
        self.__name = '{}:{}'.format(ip, port)
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(self.__host)
    
    #Public Properties
    @property
    def host(self):
        return self.__host
    @property
    def isAlive(self):
        return self.__acceptHandler is not None and self.__acceptHandler.isAlive()
    @property
    def clients(self):
        return self.__clients.copy()
    # Public Methods
    def start(self):
        self.__socket.listen(5)
        self.__acceptHandler = td.Thread(target=self.__accept_client)
        self.__acceptHandler.setDaemon(True)
        self.__acceptHandler.start()
        now = time.time()
        while not self.__acceptHandler.isAlive and (time.time() - now) <= 1:
            time.sleep(0.1)
        if self.isAlive and self.__events[jskt.EventTypes.SERVER_STARTED] is not None:
            try:
                self.__events[jskt.EventTypes.SERVER_STARTED](self)
            except Exception as ex:
                raise ex
    def stop(self):
        self.__stop = True
        self.close()
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(self.__host)
        self.__socket.close()
        # try:
        #     self.__socket.shutdown(socket.SHUT_RDWR)
        # except socket.error as ex:
        #     if ex.errno != 57 and ex.errno != 9:
        #         print(traceback.format_exc())
        self.__socket = None
        self.__acceptHandler.join(0.2)
    def bind(self, key, evt):
        if key not in self.__events:
            raise KeyError('key:\'{}\' not found!'.format(key))
        if evt is not None and not callable(evt):
            raise TypeError('evt:\'{}\' is not a function!'.format(evt))
        self.__events[key] = evt
    def send(self, data, remote=None):
        if remote is not None:
            if not self.__clients.has_key(remote):
                raise KeyError()
            elif self.__clients[remote] is None:
                raise TypeError()
            elif not self.__clients[remote].isAlive:
                raise jskt.TcpClientError()
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
        while not self.__stop:
            try:
                client, addr = self.__socket.accept()
            except socket.error as ex:
                print(traceback.format_exc())
                break
            except IOError as ex:
                print(traceback.format_exc())
                continue
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
            # print('[**] Acepted connection from: {}:{}'.format(addr[0], addr[1]))
            if self.__events[jskt.EventTypes.CONNECTED] is not None:
                try:
                    self.__events[jskt.EventTypes.CONNECTED](clk, self.__host, addr)
                except Exception as ex:
                    raise ex
        if self.__events[jskt.EventTypes.SERVER_STOPED] is not None:
            try:
                self.__events[jskt.EventTypes.SERVER_STOPED](self)
            except Exception as ex:
                raise ex
            

