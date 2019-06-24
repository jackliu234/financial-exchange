import socket
import select
import json


def broadcast_data(message):
    # this function sends a message to all sockets in the connection_list, except the server_socket.
    for socket in connection_list:
        if socket != server:
            try:
                socket.sendall(message)

            # upon exception, close the connection
            except Exception as msg:
                print("{}:{}".format(type(msg).__name__, msg))
                sock.close()
                try:
                    connection_list.remove(socket)
                except ValueError as msg:
                    print("{}:{}".format(type(msg).__name__, msg))


def print_exec_order(addr, price, quant):
    message = "\r[exchange]: trader ({}:{}) has successfully executed an limit order (price:{} quantity:{})\n".format(
        addr[0], addr[1], price, quant)
    print(message, end="")
    broadcast_data(message.encode())


def print_add_order(addr, price, quant):
    message = "\r[exchange]: trader ({}:{}) has successfully added an limit order (price:{} quantity:{})\n".format(
        addr[0], addr[1], price, quant)
    print(message, end="")
    broadcast_data(message.encode())


def add_order(data, ob):
    if len(data.decode().split()) < 4:
        pass
    else:
        filled_orders = {}

        price = int(data.decode().split()[1])
        quant = int(data.decode().split()[2])
        is_bid = data.decode().split()[3]

        if is_bid == '1':
            if price in ob['bids'].keys():
                ob['bids'][price] += quant
                print_add_order(addr, price, quant)
            else:
                for k in sorted(ob['asks']):
                    if k <= price and ob['asks'][k] - quant > 0:
                        ob['asks'][k] -= quant
                        print_exec_order(addr, k, quant)
                        quant = 0

                    elif k <= price and ob['asks'][k] - quant <= 0:
                        quant -= ob['asks'][k]
                        print_exec_order(addr, k, ob['asks'][k])
                        del ob['asks'][k]

                if quant != 0:
                    ob['bids'][price] = quant
                    print_add_order(addr, price, quant)

        elif is_bid == '0':
            if price in ob['asks'].keys():
                ob['asks'][price] += quant
                print_add_order(addr, price, quant)
            else:
                for k in reversed(sorted(ob['bids'])):
                    if k >= price and ob['bids'][k] - quant > 0:
                        ob['bids'][k] -= quant
                        print_exec_order(addr, k, quant)
                        quant = 0

                    elif k >= price and ob['bids'][k] - quant <= 0:
                        quant -= ob['bids'][k]
                        print_exec_order(addr, k, ob['bids'][k])
                        del ob['bids'][k]

                if quant != 0:
                    ob['asks'][price] = quant
                    print_add_order(addr, price, quant)


def bid_ask(ob):
    ob_disp = {'bids': {}, 'asks': {}}
    control = 0
    for k in reversed(sorted(ob['bids'])):
        if control == 3:
            continue
        else:
            ob_disp['bids'][k] = ob['bids'][k]
        control += 1

    control = 0
    for k in sorted(ob['asks']):
        if control == 3:
            continue
        else:
            ob_disp['asks'][k] = ob['asks'][k]
        control += 1

    message = "{}\n".format(
        json.dumps(ob_disp, indent=4))

    print(message, end="")
    broadcast_data(message.encode())


connection_list = []
recv_buffer = 4096

# initiate a socket instance
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind server to empty host means INADDR_ANY
port = 8000
server.bind(("", port))

# the server will listen to up to 10 connections
server.listen(10)
print("--- exchange initiated ---")
connection_list.append(server)

# create an ob for the exchange
ob = {'bids': {}, 'asks': {}}

while True:
    # use select.select to filter on the sockets that are readable (having new information)
    read_sockets, write_sockets, error_sockets = select.select(
        connection_list, [], [])

    for socket in read_sockets:
        # process new client connection (recieved through the same socket as server)
        if socket == server:
            sockfd, addr = server.accept()

            # paste the socket field to the connection list where new activities from this field will be monitor by select
            connection_list.append(sockfd)

            # print newly connected clients on server console
            # \r to prevent message overlapping
            print("\rtrader ({0}, {1}) successfully connected to the exchange".format(
                addr[0], addr[1]))

            # broadcast all new connections to all current clients
            broadcast_data("trader ({0}:{1}) successfully connected to the exchange\ninstructions:\n\tenter add_order <price> <quantity> <is_bid> to add limit orders\n\tenter bid_ask to request the current bid-ask spread on the exchange\n".format(
                addr[0], addr[1]).encode())

        # process messages received from clients
        elif socket != server:
            try:
                data = socket.recv(recv_buffer)
                if data:
                    addr = socket.getpeername()
                    message = "\r[{}:{}]: {}".format(
                        addr[0], addr[1], data.decode())
                    print(message, end="")
                    broadcast_data(message.encode())

                    if data.decode().split()[0] == "add_order":
                        add_order(data, ob)

                    elif data.decode().split()[0] == "bid_ask":
                        bid_ask(ob)

            # Errors happened, client disconnected
            except Exception as msg:
                print(type(msg).__name__, msg)
                print("\ttrader ({0}, {1}) disconnected.".format(
                    ADDR[0], ADDR[1]))
                broadcast_data("\rClient ({0}, {1}) disconnected\n".format(
                    addr[0], addr[1]).encode())
                socket.close()

                try:
                    connection_list.remove(socket)
                except ValueError as msg:
                    print("{}:{}.".format(type(msg).__name__, msg))
                continue

server.close()
