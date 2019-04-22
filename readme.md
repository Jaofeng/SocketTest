# jfNet - Custom Socket Package

|Author|Chen Jaofeng|
|---|---
|E-mail|jaofeng.chen@gmail.com

## 廢言

初學 Python 不知道要寫什麼，乾脆找以前寫過的東西來寫，寫的不好，請各位先進見諒。

小弟寫 C# 的，可能是 OO 寫的太習慣了，再加上不喜歡看太長的程式，所以凡事都喜歡用 Callback 的方式來再將基本物件再包一層，如果各位覺得多此一舉，就當小弟只是在練功，不用看得太認真... :sweat_smile:

## 目錄

* [廢言](#廢言)
* [目錄](#目錄)
* [Classes](#classes)
  * [EventTypes](#eventtypes)
  * [SocketError](#socketerror)
  * [TcpServer](#tcpserver)
  * [TcpClient](#tcpclient)
  * [CastReceiver](#castreceiver)
  * [CastSender](#castsender)
* [回呼函式格式](#回呼函式格式)
* [錯誤代碼表](#錯誤代碼表)
* [範例程式說明](#範例程式說明)
  * [Server.py](#serverpy)
  * [Client.py](#clientpy)
  * [Multicast](#multicastpy)

****

## Classes

### EventTypes

```python
class EventTypes(Enum):
    STARTED = 'onStarted'
    STOPED = 'onStoped'
    CONNECTED = 'onConnected'
    DISCONNECT = 'onDisconnect'
    RECEIVED = 'onReceived'
    SENDED = 'onSended'
    SENDFAIL = 'onSendFail'
```

回呼(callback)事件代碼列舉值，每一列舉值的意義如下：

* *STARTED* :
  * *TcpServer* : 伺服器啟動並可接受遠端連線時
  * *CastReceiver* : 多播監聽機制已啟動
* *STOPED* :
  * *TcpServer* : 伺服器停止接收連線時
  * *CastReceiver* : 多播監聽機制已停止
* *CONNECTED* :
  * *TcpServer* : 接收到遠端連線時
  * *TcpClient* : 已連接上遠端伺服器時
* *DISCONNECT* :
  * *TcpServer* : 遠端連線已關閉時
  * *TcpClient* : 與遠端伺服器斷線時
* *RECEIVED* : 接受到遠端資料時
* *SENDED* : 已將資料發送至遠端時
* *SENDFAIL* : 發送資料失敗時

****

### SocketError

```python
raise jfNet.SocketError(errno, err=None):
```

用於錯誤回傳

* *errno* : `int` - 錯誤號碼，對應說明請參閱[錯誤代碼表](#錯誤代碼表)
* *err* : `Exception` - 內部錯誤

****

### TcpServer

```python
host=('127.0.0.1', 2000)
svr = TcpServer.TcpServer(host)
```

以 TCP 為連線基礎的 Socket Server

* *host* : `tuple(str, int)` - 本端伺服器 IPv4 位址與通訊埠號

#### *TcpServer*.host

```python
ip, port = svr.host
```

取得本端伺服器的傾聽通訊埠號。***唯讀***，回傳 `tuple(ip, port)` 型別

#### *TcpServer*.isAlive

```python
if svr.isAlive:
    print('TcpServer is starting...')
else:
    print('TcpServer is stoped...')
```

取得伺服器是否處於等待連線中。***唯讀***，回傳 `True` / `False`

#### *TcpServer*.clients

```python
dic = svr.clients
for x in dic:
    print('client({}:{}) - {}'.format(x[0], x[1], dic[x]))
```

傳回已連接的連線資訊。***唯讀***，回傳 `dict{ tuple(ip, port) : <TcpClient>, ... }`

#### *TcpServer*.start()

```python
svr.start()
```

啟動 TcpServer 伺服器，開始等待遠端連線

#### *TcpServer*.stop()

```python
svr.stop()
```

停止等待遠端連線

#### *TcpServer*.bind()

```python
svr.bind(key=None, evt=None)
```

綁定回呼(callback)函式

* *key* : `str` - 回呼事件代碼，字串格式，避免錯誤引用，請直接使用 ***[EventTypes](#eventtypes)*** 列舉值
* *evt* : `def` - 回呼(callback)函式

#### *TcpServer*.close()

```python
svr.close(remote=None)
```

關閉遠端連線

* *remote* : `tuple(ip, port)` - 欲關閉連線的遠端連線位址；未傳入時，則關閉所有連線

#### *TcpServer*.send()

```python
svr.send(data, remote=None)
```

發送資料給遠端

* *data* : `str` - 欲傳送到遠端的資料
* *remote* : `tuple(ip, port)` - 欲傳送的遠端連線位址；未傳入時，則發送給所有連線

****

### TcpClient

```python
clt = TcpClient.TcpClient(socket=None, evts=None)
```

用於定義可回呼的 TCP 連線型態的 Socket Client

* *socket* : `socket` - 承接的 Socket 類別，預設為 `None`
* *evts* : `dict{str:def, ...}` - 定義 TcpClient 的回呼函式，預設為 `None`

#### *TcpClient*.recvBuffer

```python
clt.recvBuffer = 256
print('目前緩衝區設定為 {} bytes'.format(clt.recvBuffer))
```

取得或設定接收緩衝區大小，預設 256 Bytes

#### *TcpClient*.isAlive

```python
if clt.isAlive:
    print('連線中')
else:
    print('已斷線')
```

取得目前是否與伺服器連線中。***唯讀***，回傳 `True` / `False`

#### *TcpClient*.host

```python
ip, port = clt.host
```

取得本端的通訊埠號。***唯讀***，回傳 `tuple(ip, port)` 型別

#### *TcpClient*.remote

```python
ip, port = clt.remote
```

取得遠端的通訊埠號。***唯讀***，回傳 `tuple(ip, port)` 型別

#### *TcpClient*.connect()

```python
host = ('127.0.0.1', 12345)
clt.connect(host)
```

連線至遠端伺服器

* *host* : ``tuple(ip, port)`` - 遠端伺服器連線位址與通訊埠號

#### *TcpClient*.bind()

```python
clt.bind(key=None, evt=None)
```

綁定回呼(callback)函式

* *key* : `str` - 回呼事件代碼，字串格式，避免錯誤引用，請直接使用 ***[EventTypes](#eventtypes)*** 列舉值
* *evt* : `def` - 回呼(callback)函式

#### *TcpClient*.close()

```python
clt.close()
```

關閉與遠端伺服器的連線

#### *TcpClient*.send()

```python
clt.send(data)
```

發送資料至遠端伺服器

* *data* : `str` - 欲傳送到伺服器的資料

****

### CastReceiver

```python
mcRec = CastReceiver.CastReceiver(host, evts=None)
```

建立一個接收 Multicast 多播的連線類別

* *host* : `tuple(ip, port)` - 本端監聽的 IPv4 位址與通訊埠號
* *evts* : `dict{str:def, ...}` - 定義 CastReceiver 的回呼函式，預設為 `None`

#### *CastReceiver*.recvBuffer

```python
mcRec.recvBuffer = 256
print('目前緩衝區設定為 {} bytes'.format(mcRec.recvBuffer))
```

取得或設定接收緩衝區大小，預設 256 Bytes

#### *CastReceiver*.groups

```python
for x in mcRec.groups:
    print('Joined : {}'.format(x))
```

取得已註冊監聽的群組 IP。***唯讀***，回傳 `list(str, ...)` 型別

#### *CastReceiver*.host

```python
ip, port = mcRec.host
```

取得本端的通訊埠號。***唯讀***，回傳 `tuple(ip, port)` 型別

#### *CastReceiver*.isAlive

```python
if mcRec.isAlive:
    print('監聽中')
else:
    print('已停止監聽')
```

取得多播監聽器是否處於監聽中。***唯讀***，回傳 `True` / `False`

#### *CastReceiver*.reuseAddr

```python
mcRec.reuseAddr = True
print('位址 "{}" 重複使用'.format('可以' if mcRec.reuseAddr else '不可'))
```

取得或設定是否可重複綁定同一 IP 位置，預設為 `True`

#### *CastReceiver*.reusePort

```python
mcRec.reusePort = True
print('通訊埠 "{}" 重複使用'.format('可以' if mcRec.reusePort else '不可'))
```

取得或設定是否可重複綁定同一通訊埠號，預設為 `False`

#### *CastReceiver*.start()

```python
mcRec.start()
```

啟動多播監聽伺服器

#### *CastReceiver*.stop()

```python
mcRec.stop()
```

停止監聽

#### *CastReceiver*.joinGroup()

```python
mcRec.joinGroup(*ips)
```

加入監聽IP

* *ips* : `list(str, )` - 欲加入監聽的 IP 清單

#### *CastReceiver*.dropGroup()

```python
mcRec.dropGroup(*ips)
```

移除監聽 IP

* *ips* : `list(str, )` - 欲移除監聽的 IP 清單

#### *CastReceiver*.bind()

```python
mcRec.bind(key=None, evt=None)
```

綁定回呼(callback)函式

* *key* : `str` - 回呼事件代碼，字串格式，避免錯誤引用，請直接使用 ***[EventTypes](#eventtypes)*** 列舉值
* *evt* : `def` - 回呼(callback)函式

****

### CastSender

```python
mcSnd = CastSender.CastSender(evts=None)
```

建立一個發送 Multicast 多播的連線類別

* *evts* : `dict{str:def, ...}` - 定義 CastSender 的回呼函式，預設為 `None`

#### *CastSender*.bind()

```python
mcSnd.bind(key=None, evt=None)
```

綁定回呼(callback)函式

* *key* : `str` - 回呼事件代碼，字串格式，避免錯誤引用，請直接使用 ***[EventTypes](#eventtypes)*** 列舉值
* *evt* : `def` - 回呼(callback)函式

#### *CastSender*.send()

```python
mcSnd.send(remote, data)
```

發送資料至多播群組中

* *remote* : `tuple(ip, port)` - 多播位址
* *data* : `str` - 欲傳送到伺服器的資料

****

## 回呼函式格式

為提供 jfNet 所有類別物件的事件回傳，請使用以下格式定義回呼函式：

```python
def callbackName(*args):
    pass
```

* *callbackName* : 函式名稱
* *args* : 回傳之參數 list

每個類別支援的事件與回傳的參數內容不盡相同，其詳細內容如下：

* **TcpServer**
  * *STARTED* : `(<TcpServer>)`
  * *STOPED* : `(<TcpServer>)`
  * *CONNECTED* : `(<TcpClient>, host=<tuple(ip, port)>, remote=<tuple(ip, port)>)`
  * *DISCONNECT* : `(<TcpClient>, host=<tuple(ip, port)>, remote=<tuple(ip, port)>)`
  * *RECEIVED* : `(<TcpClient>, data=<str>)`
  * *SENDED* : `(<TcpClient>, data=<str>)`
  * *SENDFAIL* : `(<TcpClient>, data=<str>, err=<Exception>)`
* **TcpClient**
  * *CONNECTED* : `(<TcpClient>, host=<tuple(ip, port)>, remote=<tuple(ip, port)>)`
  * *DISCONNECT* : `(<TcpClient>, host=<tuple(ip, port)>, remote=<tuple(ip, port)>)`
  * *RECEIVED* : `(<TcpClient>, data=<str>)`
  * *SENDED* : `(<TcpClient>, data=<str>)`
  * *SENDFAIL* : `(<TcpClient>, data=<str>, err=<Exception>)`
* **CastReceiver**
  * *STARTED* : `(<CastReceiver>)`
  * *STOPED* : `(<CastReceiver>)`
  * *RECEIVED* : `(<CastReceiver>, data=<str>)`
* **CastSender**
  * *SENDED* : `(<CastSender>, data=<str>)`
  * *SENDFAIL* : `(<CastSender>, data=<str>, err=<Exception>)`

****

## 錯誤代碼表

|錯誤代碼|錯誤說明|
|:---:|---|
|1000|連線已存在|
|1001|遠端連線已斷開，或尚未連線|
|1002|位址已存在|
|1003|位址不存在|
|1004|[多播]位址不正確，應為 224.0.0.0 ~ 239.255.255.255|
|1005|[多播]此位址已在使用中，請使用 reuseAddr 與 reusePort|

****

## 範例程式說明

### Server.py

### Client.py

### Multicast.py
