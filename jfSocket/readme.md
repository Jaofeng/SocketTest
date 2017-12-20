jfSocket - TcpServer & TcpClient Package
===

|Author|Chen Jaofeng|
|---|---
|E-mail|jaofeng.chen@gmail.com


# class EventTypes(Enum):
```python
class EventTypes(Enum):
    SERVER_STARTED = 'onStarted'
    SERVER_STOPED = 'onStoped'
    CONNECTED = 'onConnected'
    DISCONNECT = 'onDisconnect'
    RECEIVED = 'onReceived'
    SENDED = 'onSended'
    SENDFAIL = 'onSendFail' 
```
回呼(callback)事件代碼列舉值，每一列舉值的意義如下：
* *SERVER_STARTED* : TcpServer 伺服器啟動並可接受遠端連線時
* *SERVER_STOPED* : TcpServer 伺服器停止接收連線時
* *CONNECTED* : 
    * *For TcpServer* : 接收到遠端連線時
    * *For TcpClient* : 已連接上遠端伺服器時
* *DISCONNECT* :
    * *For TcpServer* : 遠端連線已關閉時
    * *For TcpClient* : 與遠端伺服器斷線時
* *RECEIVED* : 接受到遠端資料時
* *SENDED* : 已將資料發送至遠端時
* *SENDFAIL* : 發送資料失敗時


# class TcpSocketError(Exception):
```python
class TcpSocketError(Exception):
    pass
```
用於錯誤回傳

# class TcpServer(object):
## Properties:
### host(readonly)
```python
TcpServer.host
```
取得本端伺服器的傾聽通訊埠號  
**唯讀**，回傳 `tuple(ip, port)` 型別

### isAlive(readonly)
```python
TcpServer.isAlive
```
取得伺服器是否處於等待連線中  
**唯讀**，回傳 `True` / `False`

### clients(readonly)
```python
TcpServer.clients
```
傳回已連接的連線資訊  
**唯讀**，回傳 `dictionary{ tuple(ip, port) : <TcpClient>, ... }`

## Functions:
### TcpServer()
```python
TcpServer.TcpServer(ip, port)
```
建立 TcpServer 類別
* *ip* : `str` - 本端 IP  
* *port* : `int` - 通訊埠號

### start()
```python
TcpServer.start()
```
啟動 TcpServer 伺服器，開始等待遠端連線

### stop()
```python
TcpServer.stop()
```
停止等待遠端連線

### bind()
```python
TcpServer.bind(key=Enum(EventTypes), evt=def)
```
綁定回呼(callback)函式
* *key* : `str` - 回呼事件代碼，字串格式，避免錯誤引用，請直接使用 ***EventTypes*** 列舉值
* *evt* : `def` 回呼(callback)函式

### close()
```python
TcpServer.close(remote=None)
```
關閉遠端連線
* *remote* : `tuple(ip, port)` - 欲關閉連線的遠端連線位址；未傳入時，則關閉所有連線

### send()
```python
TcpServer.send(data, remote=None)
```
發送資料至遠端
* *data* : `str` - 欲傳送到遠端的資料
* *remote* : `tuple(ip, port)` - 欲傳送的遠端連線位址；未傳入時，則發送給所有連線

# class TcpClient(object):
## Properties:
### isAlive(readonly)
```python
TcpClient.isAlive
```
取得目前是否與伺服器連線中  
**唯讀**，回傳 `True` / `False`

### host(readonly)
```python
TcpClient.host
```
取得本端的通訊埠號  
**唯讀**，回傳 `tuple(ip, port)` 型別

### remote(readonly)
```python
TcpClient.remote
```
取得遠端的通訊埠號  
**唯讀**，回傳 `tuple(ip, port)` 型別

## Functions:
### connect()
```python
TcpClient.connect(ip, port)
```
連線至遠端伺服器
* **ip** : `str` - 遠端伺服器連線位址
* **port** : `int` - 遠端伺服器的通訊埠號

### bind()
```python
TcpClient.bind(key=Enum(EventTypes), evt=def)
```
綁定回呼(callback)函式
* *key* : `str` - 回呼事件代碼，字串格式，避免錯誤引用，請直接使用 ***EventTypes*** 列舉值
* *evt* : `def` 回呼(callback)函式

### close()
```python
TcpClient.close()
```
關閉與遠端伺服器的連線

### send()
```python
TcpClient.send(data)
```
發送資料至遠端伺服器
* *data* : `str` - 欲傳送到的資料

# 回呼(Callback)函式格式定義
為提供 TcpServer 與 TcpClient 的事件回傳，請參閱以下格式定義回呼函式：
```python
def callbackName(*args):
    pass
```
* *callbackName* : 函式名稱
* *args* : 回傳之參數 list

每個事件回傳的參數內容不盡相同，其內容如下：
* *SERVER_STARTED* : `(<TcpServer>)`
* *SERVER_STOPED* : `(<TcpServer>)`
* *CONNECTED* : `(<TcpClient>, host=<tuple(ip, port)>, remote=<tuple(ip, port)>)`
* *DISCONNECT* : `(<TcpClient>, host=<tuple(ip, port)>, remote=<tuple(ip, port)>)`
* *RECEIVED* : `(<TcpClient>, data=<str>)`
* *SENDED* : `(<TcpClient>, data=<str>)`
* *SENDFAIL* : `(<TcpClient>, data=<str>, err=<Exception>)`



