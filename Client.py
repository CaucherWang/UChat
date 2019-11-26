import socket
import ThreadPool
import sys
from Encryption import encryptPasswd, encodeId, decodeId, pad
from Settings import HOST, PORT, COMMAND_CODE, readMessage

client_thread_pool = ThreadPool.ThreadPool(2, False)


# TODO:GUI here to present information and make changes
def Listen(conn):
    conn = conn[0]
    while True:
        data = conn.recv(1024)
        Command = int.from_bytes(data[0:2], byteorder='big')
        if Command in COMMAND_CODE.keys():
            print(Command, '  ', COMMAND_CODE[Command])
            if Command == 302:
                message = readMessage(data[18:])
                if not message:
                    print("RECEIVE DATA WITH NO END")
                    continue
                print(decodeId(data[2:18]), ': ', message)
            elif Command == 306:
                conn.close()
                break
            print('\n')
        else:
            print("ERROR: NO VALID COMMAND")
            print("DATA: ", data)


def Write(conn):
    conn = conn[0]
    while True:
        # TODO: REQUEST FORM GUI
        request = input('request:')
        if request == 'MES':
            room_no = int(input('room_no:'))
            command = int.to_bytes(102, 2, byteorder='big')
            room_number = int.to_bytes(room_no, 4, byteorder='big')
            data = input("data:")
            msg = command + room_number + (data+'###').encode('utf-8')
            conn.sendall(msg)
        elif request == "CRR":
            room_no = int(input('room_no:'))
            room_name = input("room_name:")
            command = int.to_bytes(103, 2, byteorder='big')
            room_number = int.to_bytes(room_no, 4, byteorder='big')
            msg = command + room_number + room_name.encode('ascii')
            conn.sendall(msg)
        elif request == 'JOI':
            room_no = int(input('room_no:'))
            command = int.to_bytes(104, 2, byteorder='big')
            room_number = int.to_bytes(room_no, 4, byteorder='big')
            msg = command + room_number
            conn.sendall(msg)
        elif request == 'QUI':
            room_no = int(input('room_no:'))
            command = int.to_bytes(105, 2, byteorder='big')
            room_number = int.to_bytes(room_no, 4, byteorder='big')
            msg = command + room_number
            conn.sendall(msg)
        elif request == 'OUT':
            command = int.to_bytes(106, 2, byteorder='big')
            conn.sendall(command)
            break
        else:
            print("INVALID COMMAND")


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
err_no = client.connect_ex((HOST, PORT))
if err_no:
    print("CONNECT ERROR ", err_no)
    sys.exit(err_no)
# TODO: get request from GUI
while True:
    request = input("request:")
    if request == 'LOG':
        user_id = input("user_id:")
        password = input("password:")
        command = int.to_bytes(100, 2, byteorder='big')
        user_id = encodeId(user_id)
        password = encryptPasswd(password)
        login_msg = command + user_id + password
        client.sendall(login_msg)
        data = client.recv(2)
        result_message = int.from_bytes(data, byteorder='big')
        if result_message == 300:
            print(COMMAND_CODE[300])
            client_thread_pool.addTask(Listen, client)
            client_thread_pool.addTask(Write, client)
            for i in client_thread_pool.thread_set:
                i.join()
            continue
        elif result_message in {401, 402, 403, 404}:
            print(COMMAND_CODE[result_message])
            continue
        else:
            continue
    elif request == 'REG':
        user_id = input("user_id:")
        password = input("password:")
        command = int.to_bytes(101, 2, byteorder='big')
        user_id = encodeId(user_id)
        password = encryptPasswd(password)
        register_msg = command + user_id + password
        client.sendall(register_msg)
        data = client.recv(2)
        result_message = int.from_bytes(data, byteorder='big')
        if result_message == 301:
            print(COMMAND_CODE[301])
            continue
        elif result_message == 411:
            print(COMMAND_CODE[result_message])
            continue
    elif request == 'LEA':
        sys.exit(0)
    else:
        print(COMMAND_CODE[202])
