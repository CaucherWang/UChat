import tkinter as tk
import tkinter.messagebox
import socket
import time
import threading
import queue
import sys
from Encryption import encryptPasswd, encodeId, decodeId, pad, readMessage, readRoomList, readUserList
from Settings import HOST, PORT, COMMAND_CODE
import ThreadPool

client_thread_pool = ThreadPool.ThreadPool(3, True)
MessageQueue = queue.Queue()
RoomsList = list()
# True for Rooms List HAVE BEEN Read, False for not
RoomsListFlag = True
UsersList = list()
# True for Users List HAVE BEEN Read, False for not
UsersListFlag = True
ReturnCode = 0
# True for message HAVE BEEN Read, False for HAVE NOT BEEN Read
ReturnCodeFlag = True
ChatRooms = dict()


def clientReceiveLogic(conn):
    global RoomsListFlag, RoomsList, ReturnCode, ReturnCodeFlag, loginPage
    conn = conn[0]
    while True:
        data = MessageQueue.get()
        Command = int.from_bytes(data[0:2], byteorder='big')
        if Command in COMMAND_CODE.keys():
            # print(Command, '  ', COMMAND_CODE[Command])
            # wait for last message to be finished
            while not ReturnCodeFlag:
                continue
            ReturnCode = Command
            ReturnCodeFlag = False
            # 3 Special Response Code
            if Command == 299:
                message = readMessage(data[36:])
                ReturnCodeFlag = True
                if not message:
                    # print("RECEIVE DATA WITH NO END")
                    continue
                loginPage.receiveMessage(int.from_bytes(data[2:6], byteorder='big'), decodeId(data[6:22]), message,
                                         data[22:36].decode('ascii'))
            # 298:new user enter the room
            # 297:an user left this room
            elif Command in {297, 298}:
                speaker_id = decodeId(data[6:22])
                room_no = int.from_bytes(data[2:6], byteorder='big')
                if Command == 298:
                    msg = speaker_id + ' enter this chatroom\n'
                else:
                    msg = speaker_id + ' has left this chatroom\n'
                ReturnCodeFlag = True
                ChatRooms[room_no].listUsers()
                loginPage.receiveMessage(room_no, speaker_id, msg, data[22:36].decode('ascii'))
            # 296: RECEIVE ROOM LIST
            elif Command == 296:
                ReturnCodeFlag = True
                loginPage.receiveRoomList(readRoomList(data[2:]))
            elif Command == 306:
                conn.close()
                break
            elif Command == 307:
                roomListRecieve(data[2:])
            elif Command == 308:
                userListRecieve(data[2:])
        else:
            tkinter.messagebox.showerror(title="ERROR", message="Invalid Command\n"
                                                                "Data: " + str(Command))


'''
Functions below are all in ReceiveLogic Thread
'''


def roomListRecieve(text):
    global RoomsListFlag, RoomsList
    while not RoomsListFlag:
        continue
    RoomsList.clear()
    RoomsList = readRoomList(text)
    RoomsListFlag = False


def userListRecieve(text):
    global UsersList, UsersListFlag
    while not UsersListFlag:
        continue
    UsersList.clear()
    UsersList = readUserList(text)
    UsersListFlag = False


'''
Logic Thread Code finished here
'''


def Listen(conn):
    conn = conn[0]
    while True:
        data = conn.recv(1024)
        MessageQueue.put(data)


'''
Functions below are in Main(Write) Thread, including GUI and code that create socket and main window
'''


def userInforInteract(user_id, password, command_code):
    global client
    command = int.to_bytes(command_code, 2, byteorder='big')
    user_id = encodeId(user_id)
    password = encryptPasswd(password)
    login_msg = command + user_id + password
    client.sendall(login_msg)
    data = client.recv(2)
    result_message = int.from_bytes(data, byteorder='big')
    return result_message


def loginSuccess():
    client_thread_pool.addTask(Listen, client)
    client_thread_pool.addTask(clientReceiveLogic, client)
    client_thread_pool.addTask(clientReceiveLogic, client)


def sendMessage(room_no, message, t):
    global ReturnCodeFlag, ReturnCode
    command = int.to_bytes(102, 2, byteorder='big')
    room_number = int.to_bytes(room_no, 4, byteorder='big')
    msg = command + room_number + t.encode('ascii') + (message + '###').encode('utf-8')
    client.sendall(msg)
    while ReturnCodeFlag or ReturnCode not in {302}:
        continue
    ReturnCodeFlag = True


def applyRoomsList():
    global RoomsList, RoomsListFlag, client, ReturnCodeFlag
    command = int.to_bytes(107, 2, byteorder='big')
    client.sendall(command)
    while ReturnCodeFlag or ReturnCode not in {307, 471}:
        continue
    if ReturnCode == 471:
        ReturnCodeFlag = True
        return False
    while RoomsListFlag:
        continue
    result = RoomsList.copy()
    RoomsList.clear()
    RoomsListFlag = True
    ReturnCodeFlag = True
    return result


def listUsers(room_no):
    global ReturnCodeFlag, ReturnCode, UsersList, UsersListFlag
    command = int.to_bytes(108, 2, byteorder='big')
    room_number = int.to_bytes(room_no, 4, byteorder='big')
    client.sendall(command + room_number)
    while ReturnCodeFlag or ReturnCode not in {308}:
        continue
    while UsersListFlag:
        continue
    result = UsersList.copy()
    UsersList.clear()
    UsersListFlag = True
    ReturnCodeFlag = True
    return result


def createRoom(room_no, room_name):
    global ReturnCodeFlag, ReturnCode
    command = int.to_bytes(103, 2, byteorder='big')
    room_number = int.to_bytes(int(room_no), 4, byteorder='big')
    msg = command + room_number + room_name.encode('ascii')
    client.sendall(msg)
    while ReturnCodeFlag or ReturnCode not in {303, 431, 432}:
        continue
    code = ReturnCode
    ReturnCodeFlag = True
    return code


def joinInRoom(room_number, time):
    global ReturnCodeFlag, ReturnCode
    command = int.to_bytes(104, 2, byteorder='big')
    room_number = int.to_bytes(room_number, 4, byteorder='big')
    msg = command + room_number + time.encode('ascii')
    client.sendall(msg)
    while ReturnCodeFlag or ReturnCode not in {304, 441}:
        continue
    code = ReturnCode
    ReturnCodeFlag = True
    return code


def leaveRoom(room_no, time):
    global ReturnCode, ReturnCodeFlag
    command = int.to_bytes(105, 2, byteorder='big')
    room_number = int.to_bytes(room_no, 4, byteorder='big')
    msg = command + room_number + time.encode('ascii')
    client.sendall(msg)
    while ReturnCodeFlag or ReturnCode not in {305, 451}:
        continue
    code = ReturnCode
    ReturnCodeFlag = True
    return code


def logout():
    global client
    command = int.to_bytes(106, 2, byteorder='big')
    client.sendall(command)


'''
Log in Page
'''


class LoginPage:
    def __init__(self, main_window):
        self.root = main_window
        self.root.geometry('400x300')
        self.backgroundPhoto = tk.PhotoImage(file='bgphoto.png')
        self.canvas = tk.Frame(main_window, width=400, height=300)
        self.canvas.grid()
        self.canvas.pack_propagate(0)

        self.welcomeBar = tk.Label(self.canvas, text='Welcome to UChat', image=self.backgroundPhoto, compound=tk.CENTER,
                                   fg='pink', font=('Consolas', 22),
                                   width=400, height=100)
        self.welcomeBar.pack()
        tk.Label(self.canvas, text='User name:', font=('Arial', 12)).place(x=20, y=120)
        tk.Label(self.canvas, text='Password:', font=('Arial', 12)).place(x=20, y=170)
        self.userIdRegion = tk.Entry(self.canvas, show=None, font=('Arial', 14))
        self.userIdRegion.place(x=110, y=120)
        self.passwordRegion = tk.Entry(self.canvas, show='*', font=('Arial', 14))
        self.passwordRegion.place(x=110, y=170)

        self.loginButton = tk.Button(self.canvas, text='登陆', font=('Microsoft YaHei', 12), width=10, height=1,
                                     bg='#00BFFF', bd=1, fg='white', activebackground='#87CEEB',
                                     command=self.hitLogin, relief='ridge')
        self.loginButton.place(x=160, y=210)
        self.registerButton = tk.Button(self.canvas, text='注册', font=('Microsoft YaHei', 12), width=10, height=1, bd=1,
                                        command=self.hitRegister)
        self.registerButton.place(x=160, y=250)

    def hitLogin(self):
        userId = self.userIdRegion.get()
        password = self.passwordRegion.get()
        result_message = userInforInteract(userId, password, 100)
        if result_message == 300:
            loginSuccess()
            self.canvas.destroy()
            self.roomSelectPage = RoomSelectPage(self.root)
        elif result_message in {401, 402, 403, 404}:
            tkinter.messagebox.showerror(title="LOG IN FAIL", message=COMMAND_CODE[result_message] +
                                                                      "\nUser: " + userId + "\nPassword: " + password)
        else:
            tkinter.messagebox.showerror(title="LOG IN FAIL", message="Invalid Server Command\n"
                                                                      "User: " + userId + "\nPassword: " + password)

    def hitRegister(self):
        userId = self.userIdRegion.get()
        password = self.passwordRegion.get()
        result_message = userInforInteract(userId, password, 101)
        if result_message == 301:
            tkinter.messagebox.showinfo(title="Register Success", message="Register New User Success!\n"
                                                                          "User: " + userId + "\nPassword: " + password)
        elif result_message == 411:
            tkinter.messagebox.showerror(title="Register Fail", message="User ID has Existed!\n"
                                                                        "User: " + userId)

    def receiveMessage(self, room_no, speaker, message, time):
        self.roomSelectPage.receiveMessage2(room_no, speaker, message, time)

    def receiveRoomList(self, room_list):
        self.roomSelectPage.displayRoomList(room_list)


'''
Room Select Page
'''


class RoomSelectPage:
    def __init__(self, main_window):
        self.root = main_window
        self.root.geometry('800x600')
        self.backgroundPhoto = tk.PhotoImage(file='bgphoto.png')
        self.canvas = tk.Frame(main_window, width=800, height=600)
        self.canvas.grid()
        self.canvas.pack_propagate(0)
        self.welcomeBar = tk.Label(self.canvas, text='Here is the room list', image=self.backgroundPhoto,
                                   compound=tk.CENTER, fg='pink', font=('Consolas', 22),
                                   width=800, height=200)
        self.welcomeBar.pack()
        self.loginButton = tk.Button(self.canvas, text='刷新房间列表', font=('Microsoft YaHei', 16), width=10, height=1,
                                     bg='#00BFFF', bd=1, fg='white', activebackground='#87CEEB',
                                     command=self.hitRooms)
        self.loginButton.place(x=600, y=300)
        self.inRoomButton = tk.Button(self.canvas, text='进入房间', font=('Microsoft YaHei', 16), width=10, height=1,
                                      bg='#00BFFF', bd=1, fg='white', activebackground='#87CEEB',
                                      command=self.hitinRooms)
        self.inRoomButton.place(x=600, y=400)
        self.createRoomButton = tk.Button(self.canvas, text='创建新房间', font=('Microsoft YaHei', 16), width=10, height=1,
                                          bg='#00FA9A', bd=1, fg='white', activebackground='#87CEEB',
                                          command=self.hitCreateRoom)
        self.createRoomButton.place(x=600, y=500)
        self.logoutButton = tk.Button(self.canvas, text='退出UChat', font=('Microsoft YaHei', 16), width=10, height=1,
                                      bg='#FF6347', bd=1, fg='black', activebackground='#FFA07A',
                                      command=self.logout)
        self.logoutButton.place(x=20, y=220)
        self.intVar = tk.IntVar()
        self.selectRoomNumber = 0
        self.roomList = []
        self.sonWindow = dict()
        self.hitRooms()

    def hitRooms(self):
        room_list = applyRoomsList()
        self.displayRoomList(room_list)

    def displayRoomList(self, room_list):
        for button in self.roomList:
            button.destroy()
        self.roomList.clear()
        start_pos = 300
        for room in room_list:
            tmp = tk.Radiobutton(self.canvas, text=str(room[0]) + ': ' + room[1], variable=self.intVar, value=room[0],
                                 font=('Microsoft YaHei', 13),
                                 command=self.selectRoomChange)
            self.roomList.append(tmp)
            tmp.place(x=70, y=start_pos)
            start_pos += 40
        self.intVar.set(room_list[0][0])

    def selectRoomChange(self):
        self.selectRoomNumber = self.intVar.get()

    def hitinRooms(self):
        room_no = self.selectRoomNumber
        result_message = joinInRoom(room_no, time.strftime("%m-%d %H:%M:%S", time.localtime()))
        if result_message == 304:
            room_window = tk.Toplevel(self.canvas)
            room_window.geometry('800x600')
            room_window.title('UChat-ChatRooms:' + str(room_no))
            room_window.grid()
            room_window.pack_propagate(0)
            chatRoomPage = ChatRoomPage(self, room_window, room_no)
            self.sonWindow[room_no] = chatRoomPage
        elif result_message == 441:
            tkinter.messagebox.showerror(title="Join In Room Fail", message="Room Not Exists!\n"
                                                                            "Room Number: " + str(room_no))

    def hitCreateRoom(self):
        create_window = tk.Toplevel(self.canvas)
        create_window.geometry('400x200')
        create_window.title('Create ChatRooms')
        create_window.grid()
        create_window.pack_propagate(0)
        self.create_window = create_window
        tk.Label(create_window, text='Create ChatRooms:', image=self.backgroundPhoto, compound=tk.CENTER, fg='pink', font=('Consolas', 14),
                 width=400, height=50).pack()
        tk.Label(create_window, text='Room Number:', font=('Microsoft YaHei', 10)).place(x=15, y=70)
        tk.Label(create_window, text='Room Name:', font=('Microsoft YaHei', 10)).place(x=15, y=110)
        self.roomIdRegion = tk.Entry(create_window, show=None, font=('Microsoft YaHei', 14))
        self.roomIdRegion.place(x=120, y=75)
        self.roomNameRegion = tk.Entry(create_window, show=None, font=('Microsoft YaHei', 14))
        self.roomNameRegion.place(x=120, y=115)
        createButton = tk.Button(create_window, text='创建', font=('Microsoft YaHei', 12), width=10, height=1,
                                 bg='#00BFFF', bd=1, fg='white', activebackground='#87CEEB',
                                 command=self.createRoom)
        createButton.place(x=150, y=150)

    def createRoom(self):
        room_id = self.roomIdRegion.get()
        room_name = self.roomNameRegion.get()
        result_code = createRoom(room_id, room_name)
        if result_code == 303:
            self.selectRoomNumber = int(room_id)
            self.create_window.destroy()
            self.hitinRooms()
        elif result_code == 431:
            tkinter.messagebox.showerror(title="Create Room Fail", message="Room Number Duplication!\n"
                                                                           "Room ID: " + room_id + "\nRoom Name: " + room_name)
        elif result_code == 432:
            tkinter.messagebox.showerror(title="Create Room Fail", message="Room Name Duplication!\n"
                                                                           "Room ID: " + room_id + "\nRoom Name: " + room_name)

    def receiveMessage2(self, room_no, speaker, message, time):
        self.sonWindow[room_no].msgReceive(speaker, message, time)

    def removeChild(self, son):
        self.sonWindow[son.room_no].roomWindow.destroy()
        del self.sonWindow[son.room_no]

    def logout(self):
        logout()
        self.canvas.destroy()
        self.root.destroy()
        sys.exit(0)


'''
Chat Room Page
'''


class ChatRoomPage:
    def __init__(self, parent, roomWindow, room_no):
        self.parent = parent
        self.roomWindow = roomWindow
        self.room_no = room_no
        ChatRooms[self.room_no] = self
        self.backgroundPhoto = tk.PhotoImage(file='bgphoto.png')
        self.welcomeBar = tk.Label(self.roomWindow, text='Chatroom: ' + str(room_no), image=self.backgroundPhoto,
                                   compound=tk.CENTER, width=800, height=50)
        self.buttonSend = tk.Button(self.roomWindow, text='Send', command=self.msgSend, width=10, bg='#00BFFF', bd=1,
                                    fg='white', activebackground='#87CEEB')
        self.buttonQuit = tk.Button(self.roomWindow, text='Quit', command=self.roomQuit, width=10)
        self.buttonListUsers = tk.Button(self.roomWindow, text='Users in this room', command=self.listUsers, width=20)
        self.txt_msglist = tk.Text(self.roomWindow, state='disabled', height=30, width=80)
        self.txt_msglist.tag_config('green', foreground='blue')
        self.txt_msgsend = tk.Text(self.roomWindow, height=7, width=80)
        self.txt_userslist = tk.Text(self.roomWindow, state='disabled', height=17, width=27)

        self.welcomeBar.pack()
        self.txt_msglist.place(x=10, y=60)
        self.txt_msgsend.place(x=10, y=450)
        self.txt_userslist.place(x=590, y=300)
        self.buttonListUsers.place(x=600, y=550)
        self.buttonSend.place(x=490, y=550)
        self.buttonQuit.place(x=400, y=550)

        self.listUsers()

    def listUsers(self):
        self.user_list = listUsers(self.room_no)
        self.txt_userslist.configure(state='normal')
        self.txt_userslist.delete('0.0', 'end')
        for user in self.user_list:
            self.txt_userslist.insert('end', user + '\n')
        self.txt_userslist.configure(state='disabled')

    def msgSend(self):
        msg = self.txt_msgsend.get('0.0', 'end')
        self.txt_msgsend.delete('0.0', 'end')  # 清空发送消息
        t = time.strftime("%m-%d %H:%M:%S", time.localtime())
        sendMessage(self.room_no, msg, t)
        self.txt_msglist.configure(state='normal')
        self.txt_msglist.insert('end', t + "   我:\n\t" + msg)
        self.txt_msglist.configure(state='disabled')

    def msgReceive(self, speaker, msg, time):
        self.txt_msglist.configure(state='normal')
        if time != 0:
            self.txt_msglist.insert('end', time + '\t')
        self.txt_msglist.insert('end', speaker + ' :\n\t' + msg)
        self.txt_msglist.configure(state='disabled')

    def roomQuit(self):
        result_code = leaveRoom(self.room_no, time.strftime("%m-%d %H:%M:%S", time.localtime()))
        if result_code == 305:
            del ChatRooms[self.room_no]
            self.parent.removeChild(self)


'''
Client Program Starts here!!!
'''

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
err_no = client.connect_ex((HOST, PORT))
if err_no:
    print("CONNECT ERROR ", err_no)
    sys.exit(err_no)

window = tk.Tk()
window.title('UChat_v1.0')
window.geometry('800x600')
loginPage = LoginPage(window)
window.mainloop()
