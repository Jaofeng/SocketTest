#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys, time, traceback, datetime, socket
from jfNet import CastReceiver as jcr, CastSender as jcs
from jfNet import *

_rcv = None
_snd = None
_counter = 0
_cmds = []


def toHexStr(arr):
    return ' '.join('{:02X}'.format(x) for x in arr)


def onStarted(*args):
    print(' -> Multicast Receiver Started...')


def onStoped(*args):
    print('  -> Multicast Receiver Stoped...')


def onJoinedGroup(*args):
    ip = args[1]
    print(' -> Joined {}'.format(ip))


def onReceived(*args):
    global _counter
    _counter += 1
    ipL, portL = args[2]
    ipR, portR = args[3]
    dStr = args[1]
    if isinstance(dStr, bytearray):
        dStr = toHexStr(dStr)
    print('Received Data from {}:{} -> {}:{}'.format(ipR, portR, ipL, portL))
    print('[\x1B[92m{:>3}\x1B[39m] : \x1B[97m{}\x1B[0m'.format(_counter, dStr))


def onSended(*args):
    ip,port = args[2]
    dStr = args[1]
    if isinstance(dStr, bytearray):
        dStr = toHexStr(dStr)
    print('Data has send to {}:{}\n :  {}'.format(ip, port, dStr))


def onSendfail(*args):
    ip,port = args[2]
    dStr = args[1]
    if isinstance(dStr, bytearray):
        dStr = toHexStr(dStr)
    print('Send data to {}:{} fail\n : {}\n{}'.format(ip, port, dStr, arg[3]))
    print(traceback.format_exc())


def createReceiver(*args):
    # args : Listen Port, Group Ip1, Group Ip2, ...
    global _rcv
    idx = 0
    if args[0].isdigit():
        _rcv = jcr.CastReceiver(int(args[0]))
        idx = 1
    elif isinstance(args[0], str) and len(args) >= 2 and args[1].isdigit():
        _rcv = jcr.CastReceiver((args[0], int(args[1])))
        idx = 2
    else:
        raise 'Command Error'
    _rcv.bind(key=EventTypes.STARTED, evt=onStarted)
    _rcv.bind(key=EventTypes.STOPED, evt=onStoped)
    _rcv.bind(key=EventTypes.RECEIVED, evt=onReceived)
    _rcv.bind(key=EventTypes.JOINED_GROUP, evt=onJoinedGroup)
    _rcv.joinGroup(args[idx:])
    _rcv.start()


def stopReceiver(*args):
    global _rcv
    if _rcv is not None and _rcv.isAlive:
        _rcv.stop()
    _rcv = None


def createSender(*args):
    global _snd
    _snd = jcs.CastSender()
    _snd.bind(key=EventTypes.SENDED, evt=onSended)
    _snd.bind(key=EventTypes.SENDFAIL, evt=onSendfail)


def stopSender(*args):
    global _snd
    if _snd is not None:
        _snd = None


def sendData(*args):
    global _snd
    if len(args) < 3:
        print('Missing some arg')
    addr = (args[0], int(args[1]))
    if len(args) >= 3:
        data = ''.join(args[2:])
    if data[0] == '-' and data[1] == 'x':
        data = bytearray.fromhex(data[2:])
    else:
        data = bytearray(data.encode('utf-8'))
    _snd.send(addr, data)


def joinGroup(*args):
    _rcv.joinGroup(*(args))


def dropGroup(*args):
    _rcv.dropGroup(*(args))


def waitStdin():
    global _cmds
    cmd = ''
    idx = 0
    while cmd != 'exit':
        try:
            cmd = input(': ')
            if len(cmd) == 0:
                continue
            cmds = cmd.split()
            execCommand(cmd)
            _cmds.append(cmd)
            idx = 0
        except KeyboardInterrupt:
            break
    print


def execCommand(cmd):
    global _rcv
    global _snd
    # cmd = input('Command: ')
    if len(cmd) == 0:
        return
    cmds = cmd.split()
    try:
        if cmds[0] == 'exit':
            if _snd:
                stopSender()
            if _rcv:
                stopReceiver()
        elif cmds[0] == 'start':
            if cmds[1] == 'recv':
                createReceiver(*(cmds[2:]))
            elif cmds[1] == 'send':
                createSender(*(cmds[2:]))
        elif cmds[0] == 'stop':
            if cmds[1] == 'recv' and _rcv:
                stopReceiver()
            elif cmds[1] == 'send' and _snd:
                stopSender()
        elif cmds[0] == 'join':
            joinGroup(*(cmds[1:]))
        elif cmds[0] == 'drop':
            dropGroup(*(cmds[1:]))
        elif cmds[0] == 'send':
            sendData(*(cmds[1:]))
    except:
        print(traceback.format_exc())


if __name__ == '__main__':
    print('Host Name : {}'.format(socket.gethostname()))
    _,_,ips = socket.gethostbyname_ex(socket.gethostname())
    print('Local IPs : {}'.format(', '.join(ips)))
    waitStdin()
    now = time.time()
    while (_rcv is not None or _snd is not None) and time.time() - now <= 2:
        time.sleep(0.1)
    exit(0)