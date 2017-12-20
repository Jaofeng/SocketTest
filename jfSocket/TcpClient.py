# -*- coding: UTF-8 -*-

import os, sys, time, logging, traceback, datetime
import jfSocket as jskt
import threading as td, socket

class TcpClient(object):
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
            self.assign(socket)

    # Public Properties
    @property
    def isAlive(self):
        return self.__handler is not None and self.__handler.isAlive()
    @property
    def host(self):
        return self.__host
    @property
    def remote(self):
        return self.__remote

    # Public Methods
    def assign(self, socket):
        self.socket = socket
        self.__host = socket.getsockname()
        self.__remote = socket.getpeername()
        self.__handler = td.Thread(target=self.__receiverHandler, args=(socket,))
        self.__handler.start()
    def connect(self, ip, port):
        if self.socket is not None:
            raise TcpClientError()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((ip, int(port)))
        except socket.error as err:
            raise err
        else:
            self.assign(self.socket)
            if self.__events[jskt.EventTypes.CONNECTED] is not None:
                try:
                    self.__events[jskt.EventTypes.CONNECTED](self, self.host, self.remote)
                except Exception as ex:
                    raise ex              
    def bind(self, key, evt):
        if key not in self.__events:
            raise KeyError('key:\'{}\' not found!'.format(key))
        if evt is not None and not callable(evt):
            raise TypeError('evt:\'{}\' is not a function!'.format(evt))
        self.__events[key] = evt
    def close(self):
        if self.socket is not None:
            self.socket.close()
        self.socket = None
        if self.__handler is None:
            self.__handler.join(0.2)
        self.__handler = None
    def send(self, data):
        if not self.isAlive:
            raise TcpClientError()
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
                print(traceback.format_exc())
                break
            if not data: 
                # Client Disconnect
                break
            else:
                # Received Data
                if len(data) == 0:
                    print('[**] Data length = 0')
                    break
                elif len([x for x in data if ord(x) == 0x04]) == len(data):
                    print('[**] Client terminated:({}){}'.format(len(data), data.encode('hex')))
                    break
                if self.__events[jskt.EventTypes.RECEIVED] is not None:
                    try:
                        self.__events[jskt.EventTypes.RECEIVED](self, data)
                    except Exception as ex:
                        raise ex
        if self.__events[jskt.EventTypes.DISCONNECT] is not None:
            try:
                self.__events[jskt.EventTypes.DISCONNECT](self, self.host, self.remote)
            # except Exception as ex:
            #     raise ex
            except:
                print(traceback.format_exc())

