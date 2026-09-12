#!/usr/bin/python3

import asyncio
import base64
import binascii
import hashlib


def encode_text_frame(message: str) -> bytes:
    # turn the message into bytes first so the length counts bytes not characters
    outgoing_payload = message.encode("utf-8")
    payload_length = len(outgoing_payload)

    # keeping this to short frames for now, 126+ needs extra length bytes
    if payload_length >= 126:
        error_message = "Outgoing text frames must be under 126 bytes for now"
        raise ValueError(error_message)

    # 0x81 means FIN=1 and opcode=1 (a complete text message)
    # server frames aren't masked so there's no masking key or XOR here
    header = bytes([0x81, payload_length])
    return header + outgoing_payload


def decode_text_frame(frame_data: bytes) -> str:
    # Print the raw binary exactly as the computer sees it
    # example if i type "cool" into wscat:
    # b'\x81\x84\x9b\xbf\x94Z\xf8\xd0\xfb6'
    #
    # frame_data[0] is \x81 / 10000001
    # first bit is FIN=1 so this is the final or only message fragment
    # last 4 bits are 0001 so opcode=1 which means text
    #
    # frame_data[1] is \x84 / 10000100
    # first bit is MASK=1 because browser / client frames have to be masked
    # last 7 bits are 0000100 which means the payload is 4 bytes long
    # if this was 126 or 127 the actual length would be in the next bytes
    #
    # frame_data[2:6] is b'\x9b\xbf\x94Z'
    # this is the random 4 byte masking key used to scramble the payload
    #
    # frame_data[6:] is b'\xf8\xd0\xfb6'
    # this is the actual "cool" payload but its still scrambled
    print(f"Received raw frame: {repr(frame_data)}")

    # decoding raw frames
    # decoding is a bunch of XOR opperations
    # TODO: understand the decoding opperations and format of frame data better

    # FRAME COMES IN AS
    # [header] [masking key] [scrambled message]
    # 2 Bytes  4 Bytes       wtv is left This can change later for partial / multi frames but im not worrying abt it for my use case.
    header, masking_key, payload = (
        frame_data[:2],
        frame_data[2:6],
        frame_data[6:],
    )

    # unmask the payload

    # ^ is exlusive-or or bitwise opperator in python we are going to use that to XOR with masking key

    unmasked_payload = [
        byte ^ masking_key[i % 4] for i, byte in enumerate(payload)
    ]

    # this returns unmaksed Byte values
    # use bytes() and decode() to get text conversion

    message = bytes(unmasked_payload).decode("utf-8")
    return message


async def perform_handshake(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> bool:
    # 1024 is max bytes to read in at once
    # await pauses only this client so asyncio can work on another client
    request_data = await reader.read(1024)

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
        return False

    print(http_headers)

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
    # writer.write queues the bytes and drain waits until they can be sent
    writer.write(response.encode("utf-8"))
    await writer.drain()
    return True


# need 2 loops, one for clients connecting to server, and then one for once connected
# asyncio handles the first loop and gives every client its own handle_client coroutine

# DEF couroutine
# Coroutines are computer program components that can be suspended and resumed — generalizing subroutines — for cooperative multitasking. Coroutines are well-suited for implementing familiar program components such as cooperative tasks, exceptions, event loops, iterators, infinite lists and pipes.

# They have been described as "functions whose execution you can pause".[1]


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    # reader is bytes coming from this client, writer is bytes going back to this client
    client_address = writer.get_extra_info("peername")
    print(f"\n--- New connection from {client_address} ---")

    try:
        if not await perform_handshake(reader, writer):
            return
        print(f"Handshake sent to {client_address}")

        # inner loop for actions im just going to echo back for start
        while True:
            # await pauses this client here when it has no frame data
            frame_data = await reader.read(1024)

            # If the user disconnected, frame_data will be empty
            if not frame_data:
                print("Client disconnected.")
                break

            message = decode_text_frame(frame_data)

            print(f"translated message: {message}")

            # we're then going to respond with echo client_address says "xyz"
            outgoing_frame = encode_text_frame(f'{client_address} says "{message}"')
            writer.write(outgoing_frame)
            await writer.drain()

    except (ConnectionError, UnicodeDecodeError, ValueError) as error:
        print(f"Connection ended early for {client_address}: {error}")
    finally:
        # close this client connection even if its handshake was invalid
        writer.close()
        # close queues the close, wait_closed pauses until it is actually closed
        await writer.wait_closed()


async def main() -> None:
    # https://docs.python.org/3/library/socket.html#socket-objects
    # socket.socket(family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None)
    # AF_INET = IPv4 SOCK_STREAM = TCP
    # asyncio still makes this same tcp socket for us underneath start_server

    # this line lets me reuse the port
    # bind socket to an IP / Port
    # listen for incoming, where 50 is max connection
    # asyncio also calls handle_client(reader, writer) for every accepted connection
    server = await asyncio.start_server(
        handle_client,
        "localhost",
        6969,
        reuse_address=True,
        backlog=50,
    )
    print("listening on ws://localhost:6969")

    # async with will clean up the server socket when main stops
    async with server:
        # this keeps the server running and gives the event loop time to run each client
        await server.serve_forever()


if __name__ == "__main__":
    # asyncio.run creates the event loop then starts main inside it
    asyncio.run(main())
