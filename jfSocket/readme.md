jfSocket - TcpServer & TcpClient Package
===

|Author|Chen Jaofeng|
|---|---
|E-mail|jaofeng.chen@gmail.com


# EventTypes : 
* SERVER_STARTED = 'onStarted'
* SERVER_STOPED = 'onStoped'
* CONNECTED = 'onConnected'
* DISCONNECT = 'onDisconnect'
* RECEIVED = 'onReceived'
* SENDED = 'onSended'
* SENDFAIL = 'onSendFail' 

***


# TcpServer
## Properties:
### 取得本端伺服器的傾聽通訊埠號
```python
TcpServer.host
```
唯獨，回傳 tuple(ip, port) 型別

---
### 伺服器是否處於等待連線中
```python
TcpServer.isAlive
```
唯獨，回傳 True / False

---
### 已連接的連線資訊
```python
TcpServer.clients
```
唯獨，回傳 dictionary { tuple(ip, port) : TcpClient, ... }

---
## Functions:
### 建立 TcpServer 類別
```python
TcpServer.TcpServer(ip, port)
```
* *ip* : 本端 IP  
* *port* : 通訊埠號

---
### 啟動 TcpServer 伺服器，開始等待遠端連線
```python
TcpServer.start()
```
---
### 停止 TcpServer 伺服器
```python
TcpServer.stop()
```
---

### 發送資料至遠端
```python
TcpServer.send(data, remote=None)
```
* *remote* : 欲傳送的遠端連線位址，型態為 tuple(ip, port)  

---

### 關閉遠端連線
```python
TcpServer.close(remote=None)
```
* *remote* : 欲關閉連線的遠端連線位址，型態為 tuple(ip, port)  

---

## Callback function usage :
```python
TcpServer.bind(key=Enum(EventTypes), evt=function)
```
---


#### TcpServer.bind(key, evt)