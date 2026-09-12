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

DECODING RESEARCH

• Yes, this is a specific standard: The WebSocket Protocol, RFC 6455.

The easiest reference is MDN’s Writing WebSocket servers (https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers.). Read the sections
“Format” and “Reading and unmasking the data.” After that, the authoritative specification is RFC 6455 §5.2–5.3
(https://www.rfc-editor.org/rfc/rfc6455.html#section-5.2).

The key idea is that the masked payload bytes do not have an independent meaning. They are deliberately scrambled and will usually look random.

Think of the frame as an envelope:

81 84 | 9b bf 94 5a | f8 d0 fb 36
───── ─────────── ───────────
label masking key scrambled contents

- 81 84 describes the envelope: text frame, final fragment, masked, four-byte payload.
- 9b bf 94 5a is the temporary four-byte masking key.
- f8 d0 fb 36 is the scrambled message.
- After unmasking, those final four bytes become 63 6f 6f 6c, which is UTF-8/ASCII for cool.

The mask changes for every client frame, so typing cool again will probably produce different raw bytes. That is expected. Client-to-server frames must be masked;
server-to-client frames are not masked. This behavior is defined by RFC 6455 §5.3 (https://www.rfc-editor.org/rfc/rfc6455.html#section-5.3).

Python’s byte display also makes this more confusing:

b'\x9b\xbf\x94Z'

That is still four bytes:

\x9b \xbf \x94 Z

Python displays printable bytes as characters, so Z is actually 0x5a. Similarly, the final 6 in your payload is byte 0x36, not 0x06.

For learning, these views are much clearer:

frame_data.hex()

81849bbf945af8d0fb36

list(frame_data)

[129, 132, 155, 191, 148, 90, 248, 208, 251, 54]

[f"{byte:08b}" for byte in frame_data]

['10000001', '10000100', ...]
My suggested reading order:

1. MDN: Writing WebSocket servers (https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers.) for the approachable explanation.
2. RFC 6455 §5.2 (https://www.rfc-editor.org/rfc/rfc6455.html#section-5.2) for the frame layout.
3. RFC 6455 §5.3 (https://www.rfc-editor.org/rfc/rfc6455.html#section-5.3) for masking.
4. RFC 6455 §5.6 (https://www.rfc-editor.org/rfc/rfc6455.html#section-5.6) for text versus binary payloads.
   The most important takeaway: the masked bytes are not supposed to be readable. Their only meaning is recovered after combining them with that frame’s four-byte masking
   key.

# FRONTEND

Okay weve established the server side of things for the most part its good enough.

going to add a frontend that when client connects to it starts a WS connections and streams pointer location on the screen x,y coord pair thats the goal
