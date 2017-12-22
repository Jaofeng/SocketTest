# -*- coding: UTF-8 -*-

import os, sys, time, traceback, datetime, socket
from jfSocket import EventTypes as ets, CastReceiver as jcr, CastSender as jcs

_rcv = None
_snd = None

def onStarted(*args):
    if isinstance(args[0], jcr.CastReceiver):
        print('  -> Multicast Receiver Started...')
        if len(_rcv.groups) != 0:
            print('     -> {}'.format(', '.join(_rcv.groups)))
    elif isinstance(args[0], jcr.CastSender):
        print('  -> Multicast Sender Started...')
def onStoped(*args):
    if isinstance(args[0], jcr.CastReceiver):
        print('  -> Multicast Receiver Stoped...')
    elif isinstance(args[0], jcr.CastSender):
        print('  -> Multicast Sender Stoped...')
def onReceived(*args):
    print('Received Data from {}:{}\n : {}'.format(args[2][0], args[2][1], args[1].encode('hex').upper()))
def onSended(*args):
    print('Data has send to {}:{}\n :  {}'.format(args[2][0], args[2][1], args[1].encode('hex').upper()))
def onSendfail(*args):
    print('Send data to {}:{} fail\n : {}\n{}'.format(args[2][0], args[2][1], args[1].encode('hex').upper(), args[3]))
    print(traceback.format_exc())

def createReceiver(*args):
    # args : Local IP, Listen Port, Group Ip1, Group Ip2, ...
    global _rcv
    host = (args[0], int(args[1]))
    _rcv = jcr.CastReceiver(host)
    _rcv.bind(key=ets.STARTED, evt=onStarted)
    _rcv.bind(key=ets.STOPED, evt=onStoped)
    _rcv.bind(key=ets.RECEIVED, evt=onReceived)
    for x in args[2:]:
        _rcv.joinGroup(x)
    _rcv.start()
def stopReceiver(*args):
    global _rcv
    if _rcv is not None and _rcv.isAlive:
        _rcv.stop()
    _rcv = None
def createSender(*args):
    global _snd
    _snd = jcs.CastSender()
    _snd.bind(key=ets.SENDED, evt=onSended)
    _snd.bind(key=ets.SENDFAIL, evt=onSendfail)
def stopSender(*args):
    global _snd
    if _snd is not None:
        _snd = None
def sendData(*args):
    if len(args) < 3:
        print('Missing some arg')
    addr = (args[0], int(args[1]))
    _snd.send(addr, args[2])
def joinGroup(*args):
    _rcv.joinGroup(*(args))
def dropGroup(*args):
    _rcv.dropGroup(*(args))
def waitStdin():
    global _rcv
    cmd = ''
    while cmd != 'exit':
        try:
            cmd = raw_input('Command: ')
            if len(cmd) == 0:
                continue
            cmds = cmd.split( )
            try:
                if cmds[0] == 'exit':
                    if _snd is not None:
                        stopSender()
                    if _rcv is not None:
                        stopReceiver()
                    break
                elif cmds[0] == 'start':
                    if cmds[1] == 'recv':
                        createReceiver(*(cmds[2:]))
                    elif cmds[1] == 'send':
                        createSender(*(cmds[2:]))
                elif cmds[0] == 'stop':
                    if cmds[1] == 'recv' and _rcv is not None:
                        stopReceiver()
                    elif cmds[1] == 'send' and _snd is not None:
                        stopSender()
                elif cmds[0] == 'join':
                    joinGroup(*(cmds[1:]))
                elif cmds[0] == 'drop':
                    dropGroup(*(cmds[1:]))
                elif cmds[0] == 'send':
                    sendData(*(cmds[1:]))
            except:
                print(traceback.format_exc())
            else:
                pass
        except KeyboardInterrupt:
            break
    print

def get_ip(iface = 'eth0'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    SIOCGIFADDR = 0x8915
    ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00'*14)
    try:
        res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
        return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)

if __name__ == '__main__':
    print('Host Name : {}'.format(socket.gethostname()))
    _,_,ips = socket.gethostbyname_ex(socket.gethostname())
    print('Local IPs : {}'.format(', '.join(ips)))
    waitStdin()
    now = time.time()
    while (_rcv is not None or _snd is not None) and time.time() - now <= 2:
        time.sleep(0.1)
    exit(0)