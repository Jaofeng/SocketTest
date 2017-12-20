# -*- coding: UTF-8 -*-

import os, sys, traceback, time, random, threading
from jfSocket import EventTypes as ets, TcpClient

_clients = {}
_result = {}
_times = 0

def connectToServer(*args):
    print('Connect to Server {}:{}'.format(args[0], args[1]))
    try:
        clk = TcpClient.TcpClient()
        clk.bind(key=ets.CONNECTED, evt=onConnected)
        clk.bind(key=ets.DISCONNECT, evt=onDisconnect)
        clk.bind(key=ets.RECEIVED, evt=onReceived)
        clk.bind(key=ets.SENDED, evt=onSended)
        clk.bind(key=ets.SENDFAIL, evt=onSendFail)
        clk.connect(ip=args[0], port=args[1])
    except:
        print(traceback.format_exc())
    else:
        return clk
def disconnectWithServer():
    print('Exit application...')
    try:
        for x in _clients:
            _clients[x].close()
    except:
        print(traceback.format_exc())
def onConnected(*args):
    print('  -> Connected to server, local port {}'.format(args[1][1]))
    _clients[int(args[1][1])] = args[0]
    thd = threading.Thread(target=randomThread, args=(args[0], _times, ))
    thd.start()
def onDisconnect(*args):
    addr = args[1]
    print(u'  -> Connection \u001b[32m{}:{}\u001b[0m disconnect with server...'.format(addr[0], addr[1]))
    del _clients[args[1][1]]
def onReceived(*args):
    remote = args[0].remote
    hostStr = ':'.join([str(x) for x in (args[0].host)])
    if _result.has_key(hostStr):
        print(u'  -> [{}] Received data from \u001b[32m{}:{}\u001b[0m - {:.3f}ms\n     : \u001b[35m{}\u001b[0m'.format(
            time.strftime("%H:%M:%S"), remote[0], remote[1], (time.time() - _result[hostStr]) * 1000, args[1].encode('hex')))
        del _result[hostStr]
    else:
        print(u'\u001b[40;32m  -> [{}] Received Unknow data from \u001b[32m{}:{}\u001b[0m\n     : \u001b[35m{}\u001b[0m'.format(time.strftime("%H:%M:%S"), remote[0], remote[1], args[1].encode('hex')))
def onSended(*args):
    addr = args[0].remote
    print(u'  -> [{}] Send data to \u001b[32m{}:{}\u001b[0m\n     : \u001b[34m{}\u001b[0m'.format(time.strftime("%H:%M:%S"), addr[0], addr[1], args[1].encode('hex')))
def onSendFail(*args):
    addr = args[0].remote
    print(u'  -> [{}] Send data to \u001b[32m{}:{}\u001b[0m fail\n     : \u001b[31m{}\u001b[0m'.format(time.strftime("%H:%M:%S"), addr[0], addr[1], args[1].encode('hex')))

def waitStdin():
    cmd = ''
    while cmd != 'exit':
        try:
            cmd = raw_input('client: ')
            if len(cmd) == 0:
                continue
            cmds = cmd.split( )
            try:
                if cmds[0] == 'exit':
                    disconnectWithServer()
                    break
                elif cmds[0] == 'send':
                    sendData(*(cmds[1:]))
                elif cmds[0] == 'connect':
                    if len(cmds) == 1:
                        cnt = 1
                    else:
                        cnt = int(cmds[1])
                    for _ in range(0, cnt):
                        connectToServer(*('127.0.0.1', 20000))
                        time.sleep(0.1)
                elif cmds[0] == 'close':
                    try:
                        if cmds[1] in _clients:
                            _clients[cmds[1]].close()
                    except:
                        print(traceback.format_exc())
                elif cmds[0] == 'test':
                    pressureTest(*(cmds[1:]))
                    pass
            except:
                print(traceback.format_exc())
        except KeyboardInterrupt:
            break
    print
def sendData(*args):
    try:
        if args[1] == 'str':
            _clients[int(args[0])].send(args[2])
        elif args[1] == 'hex':
            dat = ''.join(args[2:]).decode('hex')
            _clients[int(args[0])].send(dat)
    except IndexError:
        print('Command error')
    except KeyError:
        print('Connection({}) not found'.format(args[0]))
def pressureTest(*args):
    global _times
    _times = int(args[1])
    for _ in range(0, int(args[0])):
        connectToServer(*('127.0.0.1', 20000))
    while len(_clients) != int(args[0]):
        time.sleep(0.1)
    print('Connection created!!\n')
    while len(_clients) != 0:
        time.sleep(0.1)
    print(u'\u001b[2J')

def randomStr(cnt):
    res = ''
    for _ in range(0, cnt):
        res += chr(random.randint(0,255))
    return res
def randomThread(client, times):
    addr = client.host
    addrStr = ':'.join([str(x) for x in (addr)])
    for _ in range(0, times):
        time.sleep(random.uniform(0, 2) + 0.1)
        rs = randomStr(random.randint(10, 20))
        _result[addrStr] = time.time()
        client.send(rs)
        now = time.time()
        while _result.has_key(addrStr) and time.time() - now <= 2:
            time.sleep(0.05)
        if _result.has_key(addrStr):
            print(u'\u001b[31m[***] {} miss loopback!\u001b[0m'.format(addrStr))
    print(u'\u001b[32m{} Finish!!\u001b[0m'.format(addrStr))
    client.close()

if __name__ == '__main__':
    waitStdin()
    exit(0)