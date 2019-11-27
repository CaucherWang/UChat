# UChat设计文档

Contributor:

- 王泽宇 17307130038 计算机科学与技术
- 杨希希 16307130365  计算机科学与技术

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

## 1. 服务端处理逻辑

服务端主线程逻辑无限循环永不退出，每个聊天室`ChatRoom`单独一个线程，每个用户`User`单独一个线程。

### 1.1 User类与ChatRoom类

### 1.2 TCP组播机制设计

由于网络层提供的IP组播并不可靠，而聊天室需要类似TCP的可靠组播，于是需要利用现有数据结构设计TCP组播的方式。

- 设计目标：聊天室某个用户发消息，可以让处于同一聊天室的其他用户收到且仅收到一次，自己和其他人不会收到消息。

- 设计思路：发送者发送消息给服务器，服务器保留聊天室内所有用户的TCP连接；服务器收到之后在发送者线程中将消息放入房间的消息队列中；房间有单独的线程组播消息，无限循环取出消息队列的消息，依次为房间内每个用户发送消息，直到收到房间解散标志。

- 关键代码：

  ```python
  # create a room
  new_room = ChatRoom.CreateChatRoom(806, "study group")
  thread_pool.addTask(new_room.deliverMessage)
  
  # deliver a message
  if Command == 102:
      room_no = int.from_bytes(data[2:6], byteorder='big')
      user.deliverMessage(data[6:].decode('utf-8'), room_no)
  
      # in class User
      def deliverMessage(self, message, room_no):
          if room_no not in self.room_set:
              print("ROOM ", room_no, " NOT EXISTS")
              return False
          room = ChatRooms[room_no]
          room.multicast(self, message)
          return True
      
      # in class ChatRoom
      def multicast(self, speaker, message):
          self.messageQueue.put((speaker, message))
        
      # this function executed by single chatroom thread
      def deliverMessage(self):
          while True:
              if self.dissolve_flag:
                  break
              if not self.messageQueue.empty():
                  speaker, message = self.messageQueue.get()
                  conn = speaker.conn
                  for user in self.users:
                      if user != speaker:
                          conn.sendall(self.number + encodeId(speaker.name) + message)
  ```

  

## 2. 客户端处理逻辑

### 2.1 客户端线程间通信

### 2.2 主线程（Write与GUI控制线程）

### 2.3 Listen线程

​	`Listen`线程只做一件事，不断把接收到的消息整体扔到消息队列中。

### 2.4 Logic线程

​	`Logic`线程负责接收消息队列中的应答消息，依次作出反应

#### 2.4.1 无额外选项头部消息处理

​	大部分应答消息是没有额外的头部的，对于这些应答消息，只需将其返回码更新到`ReturnCode`，设置`ReturnCodeFlag==False`（未读），等待主线程功能函数读取回复。

#### 2.4.2 有额外选项头部消息处理

- `Message`：





## 3. 线程池

## 4. 数据持久化

### 4.1 MySQL模式设计

### 4.2 嵌入式SQL



## 5. 数据编码与用户数据加密

### 5.1 数据编码方式

### 5.2 DES用户数据加密

## 6. UChat协议设计

### 6.1 命令码对照表

<img src="C:\Users\64451\Pictures\md_images\image-20191127184233256.png" alt="image-20191127184233256" style="zoom:67%;" />

### 6.2 请求消息头部设计

​	所有请求消息头部都有固定的两字节的命令码，剩下均为可选部分。

- 100-用户登录：16字节`user_id`+16字节`password`。头部总长度：34Bytes
- 101-用户注册：16字节`user_id`+16字节`password`。头部总长度：34Bytes

- 102-消息发送：4字节`room_number`+16字节`speaker_id`+用户数据。头部总长度：22Bytes

- 103-创建新房间：4字节`room_number`+16字节`room_name`。头部总长度：22Bytes

- 104-加入房间：4字节`room_number`。头部总长度：6Bytes

- 105-离开某房间：4字节`room_number`。头部总长度：6Bytes

- 106-用户登出：无额外部分。头部总长度：2Bytes

- 107-列出目前所有聊天室：无额外部分。头部总长度：2Bytes

  其中，用户数据消息以连续的三个`###`作为结束标志。

  所有回应消息头部仅有2字节命令码，无其它部分。

### 6.3 应答消息头部设计

​	所有应答消息头部都有固定的两字节的命令码，剩下均为可选部分。