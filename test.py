import socket


def main():
        data = conn.recv(2)
        print(data)



server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 8900))
server.listen()
conn, address = server.accept()
main()
