# UChat设计文档

[TOC]

## 0. How to Play UChat

#### 环境搭建：

Python3, 建议 Python >= 3.6.8

cryptodome， Windows下：pycryptodome

mysql.connector

Settings.py修改`HOST`为服务器ip地址，修改`PORT`为服务器端口号

#### 运行方法：

- 服务器端首先开启数据库服务器，之后运行Server.py ；
  - 安装包：Server.py, ThreadPool.py, Settings.py, Encryption.py, ChatRoom.py
- 客户端直接运行Client.py
  - 安装包：Client.py, Settings.py, Encryption.py, ThreadPool.py 

#### 主要功能：

- 选择群组进行聊天
- 创建房间开始聊天
- 用户进入、离开房间有消息通知
- 发现房间内用户列表
- 发现房间列表

## 1. 服务端处理逻辑

服务端主线程逻辑无限循环永不退出，负责接收登陆以及注册消息；每个聊天室`ChatRoom`单独一个线程，用于组播消息；每个用户`User`服务器为其单独一个线程，负责接收已成功连接的用户请求，并进行处理。

### 1.1 User类与ChatRoom类

- `User`类负责实现服务器对用户请求的一部分处理逻辑，每个成功登陆的用户都是一个`User`类的实例，包括：
  - 加入房间
  - 创建房间
  - 发送消息（借助ChatRoom类multicast方法）
  - 离开房间
  - 用户登出
- `ChatRoom`类维护聊天室信息，存在的每个聊天室都拥有一个`ChatRoom`类的实例，并提供一些方法：
  - 加入一个用户进入房间内
  - 删除房间内一个用户
  - 返回目前房间内用户列表
  - 组播消息到房间的`messageQueue`
  - `roomDeliverMessage`方法提供TCP组播Task

### 1.2 TCP组播机制设计

由于网络层提供的IP组播并不可靠，而聊天室需要类似TCP的可靠组播，于是需要利用现有数据结构设计TCP组播的方式。

- 设计目标：聊天室某个用户发消息，可以让处于同一聊天室的其他用户收到且仅收到一次，自己和其他人不会收到消息。

- 设计思路：发送者发送消息给服务器，服务器保留聊天室内所有用户的TCP连接；服务器收到之后在发送者线程中将消息放入房间的消息队列中；房间有单独的线程组播消息，无限循环取出消息队列的消息，依次为房间内每个用户发送消息，直到收到房间解散标志。

- 示意图：

  <img src="C:\Users\64451\Pictures\md_images\image-20191201141125645.png" alt="image-20191201141125645" style="zoom:50%;" />

  

## 2. 客户端处理逻辑

### 2.1 客户端线程间通信

客户端的三类线程之间的通信依赖于共享变量。

- `MessageQueue`：Listen线程不断将消息放入`MessageQueue`,Logic线程每次从其中取出一个消息进行处理
- `ReturnCodeFlag`,`ReturnCode`：Logic解读`MessageQueue`中的消息，将收到的命令码放入`ReturnCode`，等待被主线程读取
- `UsersListFlag`,`UsersList`：Logic解释的`MEssageQueue`中的消息未必只有一个相应code，可能还带有有效信息，如果是返回的user list，应该在现有user list被主线程读取了之后更新之
- `RoomsListFlag`,`RoomsList`：返回的是room list

### 2.2 主线程（发送请求与GUI控制线程）

根据客户端的请求，发送给服务器请求消息，然后等待`return code`更新，收到信息之后再反馈给客户端响应。主线程有且只有一个

### 2.3 Listen线程

​	`Listen`线程只做一件事，不断把接收到的消息整体扔到消息队列中。Listen线程只有一个就足够了。

### 2.4 Logic线程

​	`Logic`线程负责接收消息队列中的应答消息，依次作出反应。Logic线程至少有两个，随着客户端配置，越多处理越快。当Logic线程只有一个时，接收逻辑如果需要发出请求，会发生死锁。

#### 2.4.1 无额外选项头部消息处理

​	大部分应答消息是没有额外的头部的，对于这些应答消息，只需将其返回码更新到`ReturnCode`，设置`ReturnCodeFlag==False`（未读），等待主线程功能函数读取回复。

#### 2.4.2 有额外选项头部消息处理

​	对于每个这种请求，需要用新的一组共享变量来完成，主线程读取了信息之后设为已读，Logic线程对于那些已读的消息就可以进行更新，以这种方式通知主线程收取消息。

## 3. 线程池

​	每个客户端拥有3个线程，服务器拥有N个线程，为避免服务器线程爆炸，采用线程池的设计模式。

​	线程池类`ThreadPool`每次按输入参数创建N个线程，并全部启动，线程池中有一个`workQueue`用于存放需要一个单独的线程来完成的任务，每个线程阻塞接收`workQueue`的任务，完成任务后继续接收。`workQueue`是线程安全的。

## 4. 数据持久化

​	用户信息和房间信息全部存放于服务器数据库中，以避免服务器故障后客户信息全部丢失。UChat使用MySQL数据库，建立了2张表，分别存放用户信息和房间信息。每次服务器启动时，连接数据库，以全量同步的形式缓存房间信息到内存中。

### 4.1 MySQL模式设计

<img src="C:\Users\64451\Pictures\md_images\image-20191201143448031.png" alt="image-20191201143448031" style="zoom:40%;" />

<img src="C:\Users\64451\Pictures\md_images\image-20191201143518723.png" alt="image-20191201143518723" style="zoom:40%;" />

### 4.2 嵌入式SQL

​	Python对MySQL提供了良好的支持，采用嵌入式SQL的方式用来访问和操作数据库，这里以访问用户数据来作为示例。

```python
# check information by database
def checkUser(user_id):
    DBCursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
    result = DBCursor.fetchall()  # fetchall() 获取所有记录
    if len(result) == 0:
        return False
    if len(result) > 1:
        print("DATABASE DUPLICATION")
        return False
    return result[0][0]
```

## 5. 数据编码与用户数据加密

### 5.1 数据编码方式

- 命令码：2字节编码，python内置`int.to_bytes()`函数进行编码
- 用户名：16字节编码，`ascii`编码
- 用户密码：16字节编码，DES加密编码
- 房间号：4字节编码，python内置`int.to_bytes()`函数进行编码
- 房间名：16字节编码，`ascii`编码
- 消息数据：`utf-8`编码，无字节限制，结尾以`###`为结束标志
- 房间列表：每一项20字节，4字节`room_no`，16字节`room_name`，以房间号`9999`为结束标志
- 用户列表：每一项4字节`user_name`，以`###`为结束标志

以上部分如果不足标准位置，则用空格填充.

### 5.2 DES用户数据加密

​	TCP明文传输用户密码不够安全，用DES加密技术进行加密。由服务器决定密钥，分发给客户端。双方将密码转换成`ascii`码之后进行加密。另一方收到后用密钥解密，保障安全性。

## 6. UChat协议设计

### 6.1 命令码对照表

<img src="C:\Users\64451\Pictures\md_images\image-20191201152803391.png" alt="image-20191201152803391" style="zoom:57%;" />

### 6.2 请求消息头部设计

​	所有请求消息头部都有固定的2字节的命令码，剩下均为可选部分。

- 100-用户登录：16字节`user_id`+16字节`password`。头部总长度：34Bytes

- 101-用户注册：16字节`user_id`+16字节`password`。头部总长度：34Bytes

- 102-消息发送：4字节`room_number`+14字节`send_time`+用户数据。头部总长度：20Bytes

- 103-创建新房间：4字节`room_number`+16字节`room_name`。头部总长度：22Bytes

- 104-加入房间：4字节`room_number`。头部总长度：6Bytes

- 105-离开某房间：4字节`room_number`。头部总长度：6Bytes

- 106-用户登出：无额外部分。头部总长度：2Bytes

- 107-列出目前所有聊天室：无额外部分。头部总长度：2Bytes

- 108-列出目前房间内所有用户：4字节`room_number`。头部总长度：6Bytes

  其中，用户数据消息以连续的三个`###`作为结束标志。


### 6.3 应答消息头部设计

​	所有应答消息头部都有固定的2字节的命令码加4字节的房间号加16字节`speaker_id`，剩下均为可选部分。

- 298-新用户进入房间通知消息：4字节`room_number`。头部总长度：22Bytes

