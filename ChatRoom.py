import socket
import queue
from Encryption import encodeId
from ThreadPool import ThreadPool

ChatRooms = dict()


# A user can join in many chat rooms, and deliver message
class User:
    def __init__(self, conn, name):
        self.name = name
        self.conn = conn
        self.in_room = False
        self.room_set = set()

    def joinInRoom(self, room_no, t):
        result = ChatRooms.get(room_no, False)
        if not result:
            print("ROOM ", room_no, " NOT EXISTS")
            return result
        result.joinIn(self, t)
        self.in_room = True
        self.room_set.add(room_no)
        return True

    def quitRoom(self, room_no, DBCursor, db, t):
        if room_no not in self.room_set:
            print("ROOM ", room_no, " NOT EXISTS")
            return False
        self.room_set.remove(room_no)
        result = ChatRooms.get(room_no, False)
        result.leave(self, DBCursor, db, t)
        if len(self.room_set) == 0:
            self.in_room = False
        return True

    def deliverMessage(self, message, room_no, time):
        if room_no not in self.room_set:
            print("ROOM ", room_no, " NOT EXISTS")
            return False
        room = ChatRooms[room_no]
        room.multicast(299, self, message, time)
        return True

    def logOut(self, DBCursor, db, t):
        temp = self.room_set.copy()
        for room in temp:
            self.quitRoom(room, DBCursor, db, t)
        self.room_set.clear()
        self.in_room = False
        print(self.name, "QUIT UChat")
        self.conn.close()


# each chat room need an extra thread to multicast message unlimited
class ChatRoom:
    def __init__(self, room_no, room_name):
        self.number = room_no
        self.name = room_name
        self.users = set()
        self.messageQueue = queue.Queue()
        self.dissolve_flag = False

    def listUsers(self):
        result = bytes()
        for user in self.users:
            result += encodeId(user.name)
        return result

    def joinIn(self, new_user, t):
        self.users.add(new_user)
        self.multicast(298, new_user, int.to_bytes(self.number, 4, byteorder='big'), t)

    # if a room is empty, dissolve it at once to free resource
    def leave(self, leave_user, DBCursor, db, t):
        self.users.remove(leave_user)
        if len(self.users) == 0:
            DBCursor.execute("delete from chatrooms where room_number = %s;", (self.number,))
            db.commit()
            del ChatRooms[self.number]
            self.dissolve_flag = True
            return
        self.multicast(297, leave_user, int.to_bytes(self.number, 4, byteorder='big'), t)

    def multicast(self, multicode, speaker, message, t):
        self.messageQueue.put((multicode, speaker, message, t))

    def roomDeliverMessage(self):
        while True:
            if self.dissolve_flag:
                break
            if not self.messageQueue.empty():
                multicode, speaker, message, t = self.messageQueue.get()
                for user in self.users:
                    if user != speaker:
                        if t == 0:
                            user.conn.sendall(
                                int.to_bytes(multicode, 2, byteorder='big') + int.to_bytes(self.number, 4,
                                                                                           byteorder='big') + encodeId(
                                    speaker.name) + message)
                        else:
                            user.conn.sendall(
                                int.to_bytes(multicode, 2, byteorder='big') + int.to_bytes(self.number, 4,
                                                                                           byteorder='big') + encodeId(
                                    speaker.name) + t + message)


def CreateChatRoom(room_no, DBCursor, db, thread_pool, room_name='Undefined', flag=True):
    if room_no in ChatRooms:
        print("Create ROOM ", room_no, "Fail.")
        return 431
    for key in ChatRooms.keys():
        if ChatRooms[key].name == room_name:
            return 432
    new_room = ChatRoom(room_no, room_name)
    ChatRooms[room_no] = new_room
    if flag:
        DBCursor.execute("insert into chatrooms values(%s,%s);", (room_no, room_name))
        db.commit()
    thread_pool.addTask(new_room.roomDeliverMessage)
    return new_room
