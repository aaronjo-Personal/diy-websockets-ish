#!/usr/bin/python3

import socket
import hashlib
import base64
import binascii

# https://docs.python.org/3/library/socket.html#socket-objects
# socket.socket(family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None)
# AF_INET = IPv4 SOCK_STREAM = TCP
socket_object = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# this line lets me reuse the port
socket_object.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind socket to an IP / Port
socket_object.bind(("localhost", 6969))

# listen for incoming, where 50 is max connection
socket_object.listen(50)
print(f"listening on ws://localhost:6969")

# need 2 loops, one for clients connecting to server, and then one for once connected
while True:
    client_connection, client_address = socket_object.accept()
    print(f"\n--- New connection from {client_address} ---")

    # 1024 is max bytes to read in at once
    request_data = client_connection.recv(1024)

    # traffic comes in as bytes utf decode
    # we're going to split the http headers on newline
    decode_data = request_data.decode("utf-8")

    header_section = decode_data.split("\r\n")
    http_headers = {}
    # skipping first item as its the request line (ie GET / HTTP/1.1)
    for header_field in header_section[1:]:
        if header_field == "":
            break

        if ":" in header_field:
            # unpack the header vield into k,v pairs, 1 is max 1 split
            header_field, header_value = header_field.split(":", 1)
            http_headers[header_field.lower().strip()] = header_value.strip()

    expected_headers = {
        "upgrade": "websocket",
        "sec-websocket-version": "13",
    }
    client_key = http_headers.get("sec-websocket-key", "")
    try:
        decoded_client_key = base64.b64decode(client_key, validate=True)
    except binascii.Error:
        decoded_client_key = b""

    is_websocket_request = (
        header_section[0].lower().startswith("get ")
        and all(
            http_headers.get(name, "").lower() == expected_value
            for name, expected_value in expected_headers.items()
        )
        and "upgrade"
        in {
            value.strip().lower()
            for value in http_headers.get("connection", "").split(",")
        }
        and len(decoded_client_key) == 16
    )
    if not is_websocket_request:
        client_connection.close()
        continue

    print(http_headers)

    if client_key:
        # magic_string is an industry standard https://www.rfc-editor.org/info/rfc6455/
        magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        combined = client_key + magic_string
        # have to sha1 hash then nase64 encode the combined key
        accept_key = base64.b64encode(
            hashlib.sha1(combined.encode("utf-8")).digest()
        ).decode("utf-8")

        # http response to send back to client letting it know we're swapping http -> ws
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_key}\r\n"
            "\r\n"
        )

        # send to client
        client_connection.sendall(response.encode("utf-8"))
        print(f"Handshake sent to {client_address}")

        # inner loop for actions im just going to echo back for start
        while True:
            frame_data = client_connection.recv(1024)

            # If the user disconnected, frame_data will be empty
            if not frame_data:
                print("Client disconnected.")
                break

            # Print the raw binary exactly as the computer sees it
            print(f"Received raw frame: {repr(frame_data)}")
    client_connection.close()
