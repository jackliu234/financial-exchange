import socket
import select
import sys

if len(sys.argv) < 3:
    print("incorrect initiation; please enter: python3 {0} <hostname> <port>".format(
        sys.argv[0]))
    sys.exit()

host = sys.argv[1]
port = int(sys.argv[2])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.settimeout(200)

# connect to remote host
try:
    server.connect((host, port))
except Exception as msg:
    print("{}:{}".format(type(msg).__name__, msg))

print("--- connected to exchange ---")

while True:
    # a client only receive information from two sources: server and console input
    socket_list = [sys.stdin, server]

    # use select.select to filter on the sockets that are readable (having new information)
    read_sockets, write_sockets, error_sockets = select.select(
        socket_list, [], [])

    for socket in read_sockets:
        if socket == server:
            data = socket.recv(4096)
            if data:
                # print data received from host
                print(data.decode(), end="")

            else:
                print('\ndiscounted from exchange')
                sys.exit()

        elif socket == sys.stdin:
            # prompt user to enter a new message
            msg = sys.stdin.readline()

            # erase last line
            print("\x1b[1A" + "\x1b[2K", end="")

            # send message to server
            server.sendall(msg.encode())
