# -*- coding: UTF-8 -*-

import sys, traceback, time, random, threading
from jfNet import EventTypes as ets, TcpClient

_clients = {}
_result = {}
_times = 0
_timer = {}
_success = {}
_counter = {}
_svrPort = None


def connectToServer(*args):
    print('Connect to Server {}:{}'.format(*(args[0])))
    try:
        clk = TcpClient.TcpClient()
        clk.bind(key=ets.CONNECTED, evt=onConnected)
        clk.bind(key=ets.DISCONNECT, evt=onDisconnect)
        clk.bind(key=ets.RECEIVED, evt=onReceived)
        clk.bind(key=ets.SENDED, evt=onSended)
        clk.bind(key=ets.SENDFAIL, evt=onSendFail)
        clk.connect(args[0])
    except Exception:
        print(traceback.format_exc())
    else:
        return clk


def disconnectWithServer():
    print('Exit application...')
    try:
        for x in _clients:
            _clients[x].close()
    except Exception:
        print(traceback.format_exc())


def onConnected(*args):
    print('  -> Connected to server, local port {}'.format(args[1][1]))
    _clients[int(args[1][1])] = args[0]
    hostStr = ':'.join([str(x) for x in (args[0].host)])
    _timer[hostStr] = 0.0
    _counter[hostStr] = 0
    _success[hostStr] = 0
    thd = threading.Thread(target=randomThread, args=(args[0], _times, ))
    thd.start()


def onDisconnect(*args):
    addr = args[1]
    print(u'  -> Connection \u001b[32m{}:{}\u001b[0m disconnect with server...'.format(addr[0], addr[1]))
    del _clients[args[1][1]]


def onReceived(*args):
    remote = args[0].remote
    hostStr = ':'.join([str(x) for x in args[0].host])
    if hostStr in _result:
        tmr = time.time() - _result[hostStr]
        _timer[hostStr] += tmr
        _counter[hostStr] += 1
        _success[hostStr] += 1
        # print(u'  -> [{}] Received random data from \u001b[32m{}:{}\u001b[0m - {:.3f}ms\n     : \u001b[35m{}\u001b[0m'.format(
        #     time.strftime("%H:%M:%S"), remote[0], remote[1], tmr * 1000, args[1].encode('hex')))
        del _result[hostStr]
    else:
        print(u'\u001b[40;32m  -> [{}] Received data from \u001b[32m{}:{}\u001b[0m\n     : \u001b[35m{}\u001b[0m'.format(time.strftime("%H:%M:%S"), remote[0], remote[1], args[1].encode('hex')))


def onSended(*args):
    addr = args[0].remote
    print(u'  -> [{}] Send data to \u001b[32m{}:{}\u001b[0m\n     : \u001b[34m{}\u001b[0m'.format(time.strftime("%H:%M:%S"), addr[0], addr[1], args[1].encode('hex')))


def onSendFail(*args):
    addr = args[0].remote
    print(u'  -> [{}] Send data to \u001b[32m{}:{}\u001b[0m fail\n     : \u001b[31m{}\u001b[0m'.format(time.strftime("%H:%M:%S"), addr[0], addr[1], args[1].encode('hex')))


def waitStdin():
    cmd = ''
    global _clients
    global _result
    global _svrPort
    global _times
    global _timer
    global _counter
    global _success
    while cmd != 'exit':
        try:
            cmd = input('client: ')
            if len(cmd) == 0:
                continue
            cmds = cmd.split()
            try:
                if cmds[0] == 'exit':
                    disconnectWithServer()
                    break
                elif cmds[0] == 'send':
                    sendData(*(cmds[1:]))
                elif cmds[0] == 'connect':
                    if _svrPort is None:
                        print('No set server ip and port...')
                        continue
                    if len(cmds) == 1:
                        cnt = 1
                    else:
                        cnt = int(cmds[1])
                    for _ in range(0, cnt):
                        connectToServer(_svrPort)
                        time.sleep(0.1)
                elif cmds[0] == 'close':
                    try:
                        if cmds[1] in _clients:
                            _clients[cmds[1]].close()
                    except Exception:
                        print(traceback.format_exc())
                elif cmds[0] == 'set':
                    _svrPort = (cmds[1], int(cmds[2]))
                elif cmds[0] == 'test':
                    if _svrPort is None:
                        print('No set server ip and port...')
                        continue
                    _times = int(cmds[2])
                    _timer = {}
                    _counter = {}
                    _success = {}
                    td = threading.Thread(target=pressureTest, args=(int(cmds[1]), int(cmds[2]), ))
                    td.start()
            except Exception:
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


def pressureTest(connections, times):
    for _ in range(0, connections):
        connectToServer(_svrPort)
    while len(_clients) != connections:
        time.sleep(0.1)
    print('Connection created!!\n')
    for _ in range(0, connections + 5):
        print
    done = 0
    while done < connections:
        sys.stdout.write(u'\u001b[1000D')   # Move left
        sys.stdout.write(u'\u001b[{}A'.format(connections))     # Move up
        sys.stdout.flush()
        done = 0
        for x in _counter:
            progress = int(float(_counter[x]) / _times * 100)
            width = progress / 2
            print(u'\u001b[32m{}\u001b[0m [\u001b[34m{}\u001b[0m{}] {:3d}%'.format(x, ''.ljust(width, '#'), ''.ljust(50 - width, ' '), progress))
            sys.stdout.flush()
            if _counter[x] == _times:
                done += 1
    sys.stdout.write(u'\u001b[1000D')   # Move left
    sys.stdout.write(u'\u001b[{}A'.format(connections))     # Move up
    sys.stdout.flush()
    for x in _counter:
        print(u'\u001b[32m{}\u001b[0m [\u001b[34m{}\u001b[0m] {:3d}%'.format(x, ''.ljust(width, '#'), progress))
        sys.stdout.flush()
    print('All done...')
    for x in _timer:
        print(u'[**] \u001b[32m{}\u001b[0m Finish!! Use:\u001b[32m{:.3f}ms\u001b[0m, Agv:\u001b[35m{:.3f}ms\u001b[0m, Success:\u001b[36m{:-3.1f}\u001b[0m%'.format(x, _timer[x] * 1000, _timer[x]/times * 1000, float(_success[x])/times * 100))
        sys.stdout.flush()
        _clients[int(x.split(':')[1])].close()


def randomStr(cnt):
    res = ''
    for _ in range(0, cnt):
        res += chr(random.randint(0,255))
    return res


def randomThread(client, times):
    addr = client.host
    addrStr = ':'.join([str(x) for x in (addr)])
    for i in range(0, times):
        # time.sleep(random.uniform(0, 2) + 0.1)
        rs = randomStr(random.randint(10, 20))
        _result[addrStr] = time.time()
        client.send(rs)
        now = time.time()
        while addrStr in _result and time.time() - now <= 2:
            time.sleep(0.002)
        if addrStr in _result:
            _counter[addrStr] += 1
            # print(u'\u001b[31m[***]\u001b[0m \u001b[32m{}\u001b[0m \u001b[31mmiss loopback!\u001b[0m'.format(addrStr))


if __name__ == '__main__':
    waitStdin()
    exit(0)
