import socket
import threading
import queue
import mysql.connector
import time
import ThreadPool
import ChatRoom
from Settings import HOST, PORT, MAX_CONNECT, COMMAND_CODE
from Encryption import decodeId, decryptPasswd, encodeId, readMessage

# users database
UsersDB = mysql.connector.connect(
    host="127.0.0.1",  # 数据库主机地址
    user="root",  # 数据库用户名
    passwd='993759',  # 数据库密码
    database='uchat_users'
)

DBCursor = UsersDB.cursor()
thread_pool = ThreadPool.ThreadPool(2 * MAX_CONNECT, True)


def initChatRooms():
    DBCursor.execute('select * from chatrooms;')
    result = DBCursor.fetchall()
    for i in result:
        ChatRoom.CreateChatRoom(int(i[0]), DBCursor, UsersDB, thread_pool, i[1], False)
    print(ChatRoom.ChatRooms)


# connection preparation
initChatRooms()


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


def checkUserExist(user_id):
    DBCursor.execute("SELECT * FROM users where id = %s", (user_id,))
    result = DBCursor.fetchall()  # fetchall() 获取所有记录
    if len(result) == 0:
        return True
    else:
        return False


# insert a user into database
def createUser(user_id, passwd):
    DBCursor.execute("insert into users values(%s,%s)", (user_id, passwd))
    UsersDB.commit()


def listRooms(conn, code):
    room_list = ChatRoom.ChatRooms
    if len(room_list) == 0:
        send_code = int.to_bytes(471, 2, byteorder='big')
        conn.sendall(send_code)
    else:
        send_code = int.to_bytes(code, 2, byteorder='big')
        msg = send_code
        for room in room_list.keys():
            room_number = int.to_bytes(room, 4, byteorder='big')
            room_name = encodeId(room_list[room].name)
            msg = msg + room_number + room_name
        msg += int.to_bytes(9999, 4, byteorder='big')
        conn.sendall(msg)


def normalUserListen(user):
    global message_queue
    user = user[0]
    conn = user.conn
    while True:
        try:
            data = conn.recv(22)
            # VALID COMMAND: MES CRR QUI OUT
            # MES: deliver a message, followed with 2 Bytes room number and max length 1024 Bytes message data
            # CRR: create a chat room, followed with 2 Bytes room number and 4 Bytes room name
            # JOI: join in a room, followed with 2 Bytes room number
            # QUI: quit some room, followed with 2 Bytes room number
            # OUT: log out
            Command = int.from_bytes(data[0:2], byteorder='big')
            if Command == 102:
                room_no = int.from_bytes(data[2:6], byteorder='big')
                t = data[6:20]
                msg = data[20:22]+conn.recv(1024)
                text = readMessage(msg)
                if not text:
                    print("message not valid")
                user.deliverMessage((text + '###').encode('utf-8'), room_no, t)
                conn.sendall(int.to_bytes(302, 2, byteorder='big'))
            # create a room
            elif Command == 103:
                room_no = int.from_bytes(data[2:6], byteorder='big')
                room_name = data[6:22].decode('ascii').rstrip()
                new_room = ChatRoom.CreateChatRoom(room_no, DBCursor, UsersDB, thread_pool, room_name)
                if new_room == 431:
                    send_code = int.to_bytes(431, 2, byteorder='big')
                    conn.sendall(send_code)
                elif new_room == 432:
                    send_code = int.to_bytes(432, 2, byteorder='big')
                    conn.sendall(send_code)
                else:
                    listRooms(conn, 296)
                    user.joinInRoom(room_no, (time.strftime("%m-%d %H:%M:%S", time.localtime())).encode('ascii'))
                    send_code = int.to_bytes(303, 2, byteorder='big')
                    conn.sendall(send_code)
            # wants to join in a room
            elif Command == 104:
                room_no = int.from_bytes(data[2:6], byteorder='big')
                if user.joinInRoom(room_no, data[6:20]):
                    send_code = int.to_bytes(304, 2, byteorder='big')
                    # print(user.name, "joins in room ", room_no)
                    conn.sendall(send_code)
                else:
                    send_code = int.to_bytes(441, 2, byteorder='big')
                    conn.sendall(send_code)
            # leave a room
            elif Command == 105:
                room_no = int.from_bytes(data[2:6], byteorder='big')
                if user.quitRoom(room_no, DBCursor, UsersDB, data[6:20]):
                    send_code = int.to_bytes(305, 2, byteorder='big')
                    conn.sendall(send_code)
                    listRooms(conn, 296)
                else:
                    send_code = int.to_bytes(451, byteorder='big')
                    conn.sendall(send_code)
            # log out
            elif Command == 106:
                user.logOut(DBCursor, UsersDB, (time.strftime("%m-%d %H:%M:%S", time.localtime())).encode('ascii'))
                break
            # list all rooms
            elif Command == 107:
                listRooms(conn, 307)
            elif Command == 108:
                room_no = int.from_bytes(data[2:6], byteorder='big')
                result_msg = ChatRoom.ChatRooms[room_no].listUsers()
                conn.sendall(int.to_bytes(308, 2, byteorder='big') + result_msg + '###'.encode('ascii'))
            else:
                send_code = int.to_bytes(202, 2, byteorder='big')
                conn.sendall(send_code)
        except ConnectionResetError:
            user.logOut(DBCursor, UsersDB, (time.strftime("%m-%d %H:%M:%S", time.localtime())).encode('ascii'))
            break


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(MAX_CONNECT)
print('Server start listen in PORT: ', PORT)
# Every time receive a SYN, check the head for validity
# if connection success, open a thread for that
# VALID COMMAND: LOGIN, REGIS, both need user id and password
# else if illegal connection, close that
while True:
    try:
        conn, client_addr = server.accept()
        while True:
            data = conn.recv(34)
            Command = int.from_bytes(data[0:2], byteorder='big')
            if Command == 100:
                # read user id, check the format
                user_id = decodeId(data[2:18])
                if not user_id:
                    send_code = int.to_bytes(401, 2, byteorder='big')
                    conn.sendall(send_code)
                    continue
                # check whether the user id exists
                real_password = checkUser(user_id)
                if not real_password:
                    send_code = int.to_bytes(402, 2, byteorder='big')
                    conn.sendall(send_code)
                    continue
                # decode password, check the format
                passwd = decryptPasswd(data[18:34])
                if not passwd:
                    send_code = int.to_bytes(403, 2, byteorder='big')
                    conn.sendall(send_code)
                    continue
                # check whether user id and password are matched
                if passwd != real_password:
                    send_code = int.to_bytes(404, 2, byteorder='big')
                    conn.sendall(send_code)
                    continue
                # valid user! allocate thread to this connection
                send_code = int.to_bytes(300, 2, byteorder='big')
                conn.sendall(send_code)
                new_user = ChatRoom.User(conn, user_id)
                thread_pool.addTask(normalUserListen, new_user)
                break
            elif Command == 101:
                user_id = decodeId(data[2:18])
                if not user_id:
                    send_code = int.to_bytes(401, 2, byteorder='big')
                    conn.sendall(send_code)
                    continue
                result = checkUserExist(user_id)
                if not result:
                    send_code = int.to_bytes(411, 2, byteorder='big')
                    conn.sendall(send_code)
                    continue
                # decode password, check the format
                passwd = decryptPasswd(data[18:34])
                if not passwd:
                    send_code = int.to_bytes(403, 2, byteorder='big')
                    conn.sendall(send_code)
                    continue
                # Valid Register! Create a tuple in database
                send_code = int.to_bytes(301, 2, byteorder='big')
                conn.sendall(send_code)
                createUser(user_id, passwd)
            else:
                send_code = int.to_bytes(202, 2, byteorder='big')
                conn.sendall(send_code)
                continue
    except ConnectionAbortedError:
        continue
