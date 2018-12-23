# *******************************************************************
# commonFuncs
#   - Common Client/Server functions found here
# -------------------------------------------------------------------
# Author: Jeffrey Lo, Mike Souchitto, Joseph Chau
# *******************************************************************
import sys
import re
import os

# C O N S T A N T S

# Custom Protocol msgs
CODE_100 = "100 GET %d %s\r\n"
CODE_190 = "190 Cannot send %s\r\n"
CODE_200 = "200 PUT %d %d %s\r\n"
CODE_290 = "290 Cannot write %s\r\n"
CODE_300 = "300 LS %d %s\r\n"
CODE_390 = "390 Cannot list %s\r\n"
CODE_510 = "510 %d Transfer started\r\n"
CODE_520 = "520 Transfer success\r\n"
CODE_590 = "590 Transfer failed"
CODE_800 = "800 Command Error\r\n"
CODE_900 = "900 Goodbye - Closing\r\n"

# F U N C T I O N
def quit(msg, end='\n'):
    print("%s[%d]: %s" % (sys.argv[0], os.getpid(), msg), end=end, file=sys.stderr)
    sys.exit(-1)

# print msg
def pMsg(msg, end='\n'):
    print("%s[%d]: %s" % (sys.argv[0], os.getpid(), msg), end=end)

# commmand prompt
def prompt():
    return input("JMJftp> ")


# state machine for reading until newline or return characters
#   - returns pure string or None
def read_ret(sock):
    buffer_receive = bytearray()
    temp_buffer = bytes()
    while True:
        # Look for a \r
        temp_buffer = sock.recv(1)
        if not temp_buffer:
            # Connection cut
            return None
        elif temp_buffer == b'\r':
            # Look for a \n
            temp_buffer = sock.recv(1)
            if not temp_buffer:
                # Connection cut
                return None
            elif temp_buffer == b'\n':
                # Sucess!  We have a line
                return buffer_receive.decode()
            else:
                buffer_receive.append(ord(b'\r')).append(ord(temp_buffer))
        else:
            buffer_receive.append(ord(temp_buffer))

# receives the byte length on the socket.
#   - returns a bytearray of the data or None
def recv_block(sock, length):
    bytes_received = 0
    buffer_receive = bytearray()
    temp_buffer = bytes()
    while len(buffer_receive) < length:
        temp_buffer = sock.recv(length - len(buffer_receive))
        if not temp_buffer:
            return None
        buffer_receive += temp_buffer
    return buffer_receive


def split_msg(msg):
    match = re.search(r'^\s*(\d+)\s+(.+)\s*$', msg)
    if match is None: return None
    basic_split = match.groups()
    code = basic_split[0]
    # Add logic for more commands here
    if code == "100":
        match = re.search(r'^\s*(\w+)\s+(\d+)\s+(.+)\s*$', basic_split[1])
    elif code == "200":
        match = re.search(r'^\s*(\w+)\s+(\d+)\s+(\d+)\s+(.+)\s*$', basic_split[1])
    elif code == "300":
        match = re.search(r'^\s*(\w+)\s+(\d+)(?:\s+(.+))?\s*$', basic_split[1])
    elif code == "510":
        match = re.search(r'^\s*([0-9\-]+)\s+(.+)\s*$', basic_split[1])
    else:
        return basic_split
    if match is None: return None
    adv_split = [code]
    adv_split.extend(match.groups())
    return adv_split


# Send and Print the message on the socket
def send_msg(socket, msg):
    #pMsg("**send_msg \"%s\"" %(msg.strip()))
    socket.sendall(msg.encode())

# receives and prints message on the socket
def receive_msg(sock):
    raw_message = read_ret(sock)
    if raw_message is None:
        #pMsg("**receive_msg: received None - connection closed")
        return None
    #pMsg("**receive_msg: \"%s\"" %(raw_message.strip()))
    return split_msg(raw_message)
