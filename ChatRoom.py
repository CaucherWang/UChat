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

    def joinInRoom(self, room_no):
        result = ChatRooms.get(room_no, False)
        if not result:
            print("ROOM ", room_no, " NOT EXISTS")
            return result
        result.joinIn(self)
        self.in_room = True
        self.room_set.add(room_no)
        return True

    def deliverMessage(self, message, room_no):
        if room_no not in self.room_set:
            print("ROOM ", room_no, " NOT EXISTS")
            return False
        room = ChatRooms[room_no]
        room.multicast(299, self, message)
        return True

    def quitRoom(self, room_no, DBCursor, db):
        if room_no not in self.room_set:
            print("ROOM ", room_no, " NOT EXISTS")
            return False
        self.room_set.remove(room_no)
        result = ChatRooms.get(room_no, False)
        result.leave(self, DBCursor, db)
        # multicast to all users in room
        # result.multicast(self,)
        if len(self.room_set) == 0:
            self.in_room = False
        return True

    def logOut(self):
        self.room_set.clear()
        self.in_room = False
        send_code = int.to_bytes(306, 2, byteorder='big')
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
        print("in ChatRoom", result)
        return result

    def joinIn(self, new_user):
        self.users.add(new_user)
        self.multicast(298, new_user, int.to_bytes(self.number, 4, byteorder='big'))

    # if a room is empty, dissolve it at once to free resource
    def leave(self, leave_user, DBCursor, db):
        self.users.remove(leave_user)
        if len(self.users) == 0:
            DBCursor.execute("delete from chatrooms where room_number = %s;", (self.number,))
            db.commit()
            self.dissolve_flag = True
            return
        self.multicast(297, leave_user, int.to_bytes(self.number, 4, byteorder='big'))

    def multicast(self, multicode, speaker, message):
        self.messageQueue.put((multicode, speaker, message))

    def roomDeliverMessage(self):
        while True:
            if self.dissolve_flag:
                break
            if not self.messageQueue.empty():
                multicode, speaker, message = self.messageQueue.get()
                for user in self.users:
                    if user != speaker:
                        user.conn.sendall(
                            int.to_bytes(multicode, 2, byteorder='big') + int.to_bytes(self.number, 4,
                                                                                       byteorder='big') + encodeId(
                                speaker.name) + message)


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
