# -*- coding: UTF-8 -*-

import os, sys, time, traceback, datetime
import socket
from jfSocket import EventTypes as ets, TcpServer, TcpClient

_svr = None

def runServers(ip, port):
    print 'Creating Listen Server at {}:{}...'.format(ip, port)
    global _svr
    try:
        _svr = TcpServer.TcpServer(ip=ip, port=port)
    except socket.error as ex:
        if ex.errno == 48:
            print('Address already in use, please try again...')
        else:
            print(ex)
        return False
    try:
        _svr.name = '{}:{}'.format(ip, port)
        _svr.bind(key=ets.SERVER_STARTED, evt=onServerStarted)
        _svr.bind(key=ets.SERVER_STOPED, evt=onServerStoped)
        _svr.bind(key=ets.CONNECTED, evt=onClientConnected)
        _svr.bind(key=ets.DISCONNECT, evt=onClientDisconnect)
        _svr.bind(key=ets.RECEIVED, evt=onReceived)
        _svr.bind(key=ets.SENDED, evt=onSended)
        _svr.bind(key=ets.SENDFAIL, evt=onSendFail)
        _svr.start()
    except Exception as ex:
        print(ex)
        return False
    else:
        return True

def stopServer():
    print('Stop Listen Server...')
    _svr.stop()
# Callback Methods
def onServerStarted(svr):
    print('  -> Server({}) listening...'.format(svr.name))
def onServerStoped(svr):
    print('  -> Server({}) stop listen...'.format(svr.name))
def onClientConnected(*args):
    addr = args[2]
    print(u'  -> Client connected from \u001b[32m{}:{}\u001b[0m'.format(addr[0], addr[1]))
def onClientDisconnect(*args):
    addr = args[2]
    print(u'  -> Client \u001b[32m{}:{}\u001b[0m disconnect...'.format(addr[0], addr[1]))
def onReceived(*args):
    addr = args[0].remote
    print(u'  -> [{}] Received data from \u001b[32m{}:{}\u001b[0m\n     : \u001b[35m{}\u001b[0m'.format(time.strftime("%H:%M:%S"), addr[0], addr[1], args[1].encode('hex')))
    args[0].send(args[1])
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
            cmd = raw_input('server: ')
            if len(cmd) == 0:
                continue
            cmds = cmd.split( )
            try:
                if cmds[0] == 'exit':
                    if _svr is not None and _svr.isAlive:
                        stopServer()
                    break
                elif cmds[0] == 'start':
                    if _svr is not None and _svr.isAlive:
                        print('Server is listening...')
                    elif not runServers(cmds[1], int(cmds[2])):
                        break
                elif cmds[0] == 'stop':
                    if _svr is not None and _svr.isAlive:
                        stopServer()
                    else:
                        print('Server not start...')
                elif cmds[0] == 'send':
                    if _svr is not None and _svr.isAlive:
                        sendData(*(cmds[1:]))
                    else:
                        print('Server not start...')
                elif cmds[0] == 'clients':
                    if _svr is not None and _svr.isAlive:
                        showClients()
                    else:
                        print('Server not start...')
                elif cmds[0] == 'close':
                    if _svr is not None and _svr.isAlive:
                        if cmds[1] == 'all':
                            _svr.close()
                        else:
                            closeClient(*(cmds[1:]))
                    else:
                        print('Server not start...')
            except:
                print(traceback.format_exc())
            else:
                pass
        except KeyboardInterrupt:
            break
    print
def sendData(*args):
    try:
        if args[1] == 'str':
            if args[0] == 'all':
                _svr.send(args[2])
            else:
                try:
                    remote = [x for x in _svr.clients if int(x[1]) == int(args[0])][0]
                except IndexError:
                    print('Unknow client')
                else:
                    _svr.send(args[2], remote)
        elif args[1] == 'hex':
            dat = ''.join(args[2:]).decode('hex')
            if args[0] == 'all':
                _svr.sendAll(dat)
            else:
                try:
                    remote = [x for x in _svr.clients if int(x[1]) == int(args[0])][0]
                except IndexError:
                    print('Unknow client')
                else:
                    _svr.send(dat, remote)
    except IndexError:
        print('Command error')
    except KeyError:
        print('Connection({}) not found'.format(args[0]))
def showClients():
    try:
        for x in _svr.clients:
            print('{}:{}'.format(x[0], x[1]))
        print
    except:
        print(traceback.format_exc())
def closeClient(*args):
    try:
        remote = [x for x in _svr.clients if x == (args[0], int(args[1]))][0]
    except IndexError:
        print('Unknow client!')
    else:
        try:
            _svr.close(remote)
        except:
            print(traceback.format_exc())
        
    
if __name__ == '__main__':
    waitStdin()
    time.sleep(1)
    exit(0)