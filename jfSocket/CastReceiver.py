# -*- coding: UTF-8 -*-

import sys, time, traceback, errno
import jfSocket as jskt
import threading as td, socket

class CastReceiver(object):
    def __init__(self, host, evts=None):
        self.__socket = None
        self.__host = host
        self.__receiveHandler = None
        self.__stop = False
        self.__groups = []
        self.__events = {
            jskt.EventTypes.STARTED : None,
            jskt.EventTypes.STOPED : None,
            jskt.EventTypes.RECEIVED : None
        }
        if evts:
            for x in evts:
                self.__events[x] = evts[x]
        self.recvBuffer = 256

    # Public Properties
    @property
    def groups(self):
        return self.__groups[:]
    @property
    def host(self):
        return self.__host
    @property
    def isAlive(self):
        return self.__receiveHandler is not None and self.__receiveHandler.isAlive()

    # Public Methods
    def start(self):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ip,_ = self.__host
        hosts = []
        if ip == '' or ip == '0.0.0.0':
            _,_,hosts = socket.gethostbyname_ex(socket.gethostname())
        else:
            hosts.append(ip)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        for h in hosts:
            self.__socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(h))
            for x in self.__groups:
                sys.stdout.write('Monitor : {} + {}'.format(x, h))
                ms = socket.inet_aton(x) + socket.inet_aton(h)
                try:
                    self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, ms)
                except socket.error as err:
                    if err.errno == errno.EADDRINUSE:
                        print(' -> In use')
                        pass
                    else:
                        print(' -> error({})'.format(err.errno))
                        raise
                else:
                    print(' -> OK')
        self.__socket.bind(self.__host)
        self.__receiveHandler = td.Thread(target=self.__receive_handler, args=(self.__socket, ))
        self.__receiveHandler.setDaemon(True)
        self.__receiveHandler.start()
        now = time.time()
        while not self.__receiveHandler.isAlive and (time.time() - now) <= 1:
            time.sleep(0.1)
        if self.isAlive and self.__events[jskt.EventTypes.STARTED] is not None:
            try:
                self.__events[jskt.EventTypes.STARTED](self)
            except Exception as ex:
                raise
    def stop(self):
        self.__stop = True
        if self.__socket is not None:
            self.__socket.close()
        self.__socket = None
        if self.__receiveHandler is not None:
            self.__receiveHandler.join(2.5)
        self.__receiveHandler = None
    def joinGroup(self, *ips):
        for x in ips:
            if ord(socket.inet_aton(x)[0]) not in range(224, 240):
                raise jskt.SocketError(1004)
            if x in self.__groups:
                raise jskt.SocketError(1002)
            self.__groups.append(x)
            if not self.isAlive:
                continue
            ip,_ = self.__host
            hosts = []
            if ip == '' or ip == '0.0.0.0':
                _,_,ips = socket.gethostbyname_ex(socket.gethostname())
                hosts = ips[:]
            else:
                hosts.append(ip)
            for h in hosts:
                sys.stdout.write('Join {} + {}'.format(x, h))
                ms = socket.inet_aton(x) + socket.inet_aton(h)
                try:
                    self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, ms)
                except socket.error as err:
                    if err.errno == errno.EADDRINUSE:
                        print(' -> In Use')
                        pass
                    else:
                        print(' -> error({})'.format(err.errno))
                        raise
                else:
                    print(' -> OK')
    def dropGroup(self, *ips):
        restart = False
        for x in ips:
            if ord(socket.inet_aton(x)[0]) not in range(224, 240):
                raise jskt.SocketError(1004)
            if x not in self.__groups:
                raise jskt.SocketError(1003)
            self.__groups.remove(x)
            if not self.isAlive:
                continue
            ip,_ = self.__host
            hosts = []
            if ip == '' or ip == '0.0.0.0':
                _,_,ips = socket.gethostbyname_ex(socket.gethostname())
                hosts = ips[:]
            else:
                hosts.append(ip)
            for h in hosts:
                ms = socket.inet_aton(x) + socket.inet_aton(h)
                try:
                    self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, ms)
                except socket.error as err:
                    if err.errno == errno.EADDRINUSE:
                        pass
                    else:
                        raise
                else:
                    pass
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

    # Private Methods
    def __receive_handler(self, sock):
        # 使用非阻塞方式等待資料，逾時時間為 2 秒
        sock.settimeout(2)
        while not self.__stop:
            try:
                data, addr = sock.recvfrom(self.recvBuffer)
            except socket.timeout:
                # 等待資料逾時，再重新等待
                if self.__stop:
                    break
                else:
                    continue
            except Exception as ex:
                # 先攔截並顯示，待未來確定可能會發生的錯誤再進行處理
                print(traceback.format_exc())
                break
            if not data: 
                # 空資料，認定遠端已斷線
                break
            else:
                # Received Data
                if len(data) == 0:
                    # 空資料，認定遠端已斷線
                    break
                elif len([x for x in data if ord(x) == 0x04]) == len(data):
                    # 收到 EOT(End Of Transmission, 傳輸結束)，則表示已與遠端中斷連線
                    break
                if self.__events[jskt.EventTypes.RECEIVED] is not None:
                    try:
                        self.__events[jskt.EventTypes.RECEIVED](self, data, addr)
                    except Exception as ex:
                        raise ex
        if self.__events[jskt.EventTypes.STOPED] is not None:
            try:
                self.__events[jskt.EventTypes.STOPED](self)
            except Exception as ex:
                raise ex

