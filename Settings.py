HOST = '10.222.149.201'
PORT = 6666
MAX_CONNECT = 50

COMMAND_CODE = {
    100: 'LOG IN',
    101: "REGISTER",
    102: "MESSAGE",
    103: "CREATE A ROOM",
    104: "JOIN IN A ROOM",
    105: "QUIT A ROOM",
    106: "LOG OUT",
    201: "CONNECTION FAILURE",
    202: "INVALID COMMAND",
    300: "LOG IN SUCCESS",
    301: "REGISTER SUCCESS",
    302: "MESSAGE RECEIVED",
    303: "ROOM CREATED",
    304: "JOIN IN SUCCESS",
    305: "QUIT SUCCESS",
    306: "LOG OUT SUCCESS",
    401: "ILLEGAL USER ID",
    402: "NO USER ID",
    403: "ILLEGAL PASSWORD",
    404: "PASSWORD FAULT",
    411: "USER ID HAS EXISTED",
    431: "ROOM NUMBER DUPLICATION",
    432: "ROOM NAME DUPLICATION",
    441: "NO SUCH ROOM",
    451: "NO SUCH ROOM"
}


def readMessage(text):
    text = text.decode('utf-8')
    for i in range(1003):
        if text[i] == '#' and text[i + 1] == '#' and text[i + 2] == '#':
            return text[:i]
    return False
