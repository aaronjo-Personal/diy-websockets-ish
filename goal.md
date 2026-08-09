- Handroll websockets in python (using socket (who cares if cheating))

- What are websockets
  -- a protocol that allows 2 way communication over a single TCP connection

- What is TCP connection?
  -- A Transmission Control Protocol is a dedicated reliable connection to link two devices on a network

-- syn, syn-ack, ack tcp handshake etc

How do websockets?

- start?
  -- http handshake that upgrades to the websocket protocol

- close
  -- either party sends close frame

Diff between http and websockets?

- http request-response pattern websockets are persistent and bi-directional.

---

okay so how do we even start?

- start with RAW tcp server
  -- going to use python, going to use socket module

GOAL: Your goal for this phase:
-- socket that binds to a port calls listen and then runs an infinite loop using accept()

https://docs.python.org/3/library/socket.html
https://www.w3schools.com/python/ref_module_socket.asp

-- next http upgrade handshake

- Your goal for this phase:

Read the incoming bytes and decode them to an ASCII string.

Parse the string to find the Sec-WebSocket-Key header.

Import Python's built-in hashlib and base64.

Append the magic string 258EAFA5-E914-47DA-95CA-C5AB0DC85B11 to the key.

SHA-1 hash the combined string, Base64 encode it, and send back a valid HTTP/1.1 101 Switching Protocols response.

If you do this correctly, your browser's dev tools will show the WebSocket as "Connected" instead of immediately failing.

-- decoding incoming frames

Your goal for this phase:
Read the first two bytes of an incoming message.

Byte 1: Contains the FIN bit (is this the final piece of the message?) and the Opcode (is this text, binary, or a ping?).

Byte 2: Contains the Mask bit (always 1 from a browser) and the Payload Length.

pahse 4

Phase 4: Encoding Outgoing Frames (Python to Browser)
Servers do not have to mask their data, which makes this step much easier than Phase 3.

Your goal for this phase:
Take a Python string (e.g., "Hello Client!"), encode it to bytes (UTF-8), and slap the correct WebSocket header on the front.

Byte 1: 0x81 (which means FIN=1, Opcode=1 for Text).

Byte 2: The length of your string (assuming it's under 126 characters for now).

The rest of the bytes: Your UTF-8 string.
Send it down the socket!

Phase 5: The Event Loop & Opcodes
A real WebSocket server needs to handle multiple things at once and manage connection health.

Your goal for this phase:
Implement basic support for other Opcodes.

If the browser sends Opcode 8 (Close Connection), your server should cleanly shut down that socket.

If the browser sends Opcode 9 (Ping), your server must immediately reply with Opcode A (Pong) to keep the connection alive.

etc we'll worry about phase 3 + later

https://datatracker.ietf.org/doc/html/rfc6455
