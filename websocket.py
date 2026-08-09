#!/usr/bin/python3

import socket

# https://docs.python.org/3/library/socket.html#socket-objects
# socket.socket(family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None)
# AF_INET = IPv4 SOCK_STREAM = TCP
socket_object = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind socket to an IP / Port
socket_object.bind(("localhost", 6969))

# listen for incoming
socket_object.listen()
print(f"listening on ws://localhost:6969")

# event loop
while True:
    client_connection, client_address = socket_object.accept()
    print(f"\n--- New connection from {client_address} ---")

    # 1024 is max bytes to read in at once
    request_data = client_connection.recv(1024)

    # traffic comes in as bytes utf decode
    print(request_data.decode("utf-8"))

    # close connection
    client_connection.close()
