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
    107: "LIST ALL ROOMS",
    108: "LIST ALL USERS",
    201: "CONNECTION FAILURE",
    202: "INVALID COMMAND",
    299: "RECEIVE MESSAGE",
    300: "LOG IN SUCCESS",
    301: "REGISTER SUCCESS",
    302: "SENT SUCCESSFULLY",
    303: "ROOM CREATED",
    304: "JOIN IN SUCCESS",
    305: "QUIT SUCCESS",
    306: "LOG OUT SUCCESS",
    307: "RETURN ALL ROOMS",
    401: "ILLEGAL USER ID",
    402: "NO USER ID",
    403: "ILLEGAL PASSWORD",
    404: "PASSWORD FAULT",
    411: "USER ID HAS EXISTED",
    431: "ROOM NUMBER DUPLICATION",
    432: "ROOM NAME DUPLICATION",
    441: "NO SUCH ROOM",
    451: "NO SUCH ROOM",
    471: "NO ROOMS NOW",
    481: "RETURN ALL USERS"
}
