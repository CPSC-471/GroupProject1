from commonFuncs import*
from ClientSide.py import*
import socket
import os
import sys
import time
import subprocess
import signal

# 100 GET
def get(filename):
    global sock_data_welcome, sock_data
    # Allocate ephemeral port
    sock_data_welcome = setup_ephemeral_conn()
    port = sock_data_welcome.getsockname()[1]
    # Send 100 message with port number
    send_msg(sock_conn, MSG_100 %(port, filename))
    # Accept server connection
    debug("*get: Waiting for server to connect")
    sock_data, addr = sock_data_welcome.accept()
    # Wait for 510 with chunk size
    message = receive_msg(sock_conn)
    if message is None:
        pMsg("*get: Connection closed by remote host")
        teardown_data_conn()
        return False
    elif message[0] != "510" or len(message) < 2:
        teardown_data_conn()
        return False
    length = int(message[1])
    debug("*get: Server connected!  Length is %d" %(length))
    # Receive the data
    bytes_received = 0
    # MAX_BYTES should be used here instead of 512
    try:
        # Write file to the current directory, even if it is in a server subdir
        short_filename = os.path.split(filename)[1]
        fo = open(short_filename, mode='wb')
        while (bytes_received < length):
            raw_data = recv_block(sock_data, min(512, length - bytes_received))
            if raw_data is None:
                pMsg("*get: Server hung up")
                teardown_data_conn()
                return False
            bytes_received += len(raw_data)
            fo.write(raw_data)
            # MAX_BYTES should be used here instead of 512
        fo.close()
    except(OSError):
        pMsg("*get: Cannot open file")
        teardown_data_conn()
        return False
    # Receive 520 (Success!)
    message = receive_msg(sock_conn)
    if message is None:
        pMsg("*get: Connection closed by remote host")
        teardown_data_conn()
        return False
    elif message[0] != "520":
        pMsg("*get: Transfer not successful")
        teardown_data_conn()
        return False
    # TODO: ASCII art of success kid
    # Close stuff
    teardown_data_conn()
    return True

# 200 PUT
def put(path):
    global sock_data_welcome, sock_data
    # Check to make sure it is a file
    if not os.path.isfile(path):
        pMsg("*put: Not a file")
        return False
    # Get the file size.
    try:
        length = os.stat(path).st_size
        filename = os.path.split(path)[1]
    except(FileNotFoundError):
        pMsg("*put: File not found")
        return False
    # Allocate ephemeral port
    sock_data_welcome = setup_ephemeral_conn()
    port = sock_data_welcome.getsockname()[1]
    # Send 200 message with port number
    send_msg(sock_conn, MSG_200 %(port, length, filename))
    # Accept server connection
    debug("*put: Waiting for server to connect")
    sock_data, addr = sock_data_welcome.accept()
    # Wait for 510
    message = receive_msg(sock_conn)
    if message is None:
        pMsg("*put: Connection closed by remote host")
        teardown_data_conn()
        return False
    elif message[0] != "510" or len(message) < 2:
        teardown_data_conn()
        return False
    debug("*put: Server connected!  Sending %d bytes" %(length))
    # Transmit the data
    try:
        fd = open(path, "rb")
        bytessent = 0
        while bytessent < length:
            raw_data = fd.read(4096)
            debug("*put: Sending block...")
            sock_data.sendall(raw_data)
            bytessent += len(raw_data)
        fd.close()
    except(OSError):
        pMsg("*put: Cannot open file")
        teardown_data_conn()
        return False
    # Receive 520 (Success!)
    message = receive_msg(sock_conn)
    if message is None:
        pMsg("*put: Connection closed by remote host")
        teardown_data_conn()
        return False
    elif message[0] != "520":
        pMsg("*put: Transfer not successful")
        teardown_data_conn()
        return False
    # TODO: ASCII art of success kid
    # Close stuff
    teardown_data_conn()
    return True

# 300 LS
def ls(path):
    global sock_data_welcome, sock_data
    # Allocate ephemeral port
    sock_data_welcome = setup_ephemeral_conn()
    port = sock_data_welcome.getsockname()[1]
    # Send 300 message with port number
    send_msg(sock_conn, MSG_300 %(port, path))
    # Accept server connection
    debug("[ls] Waiting for server to connect")
    sock_data, addr = sock_data_welcome.accept()
    # Wait for 510 with chunk size
    message = receive_msg(sock_conn)
    if message is None:
        pMsg("[ls] Connection closed by remote host")
        teardown_data_conn()
        return False
    elif message[0] != "510" or len(message) < 2:
        teardown_data_conn()
        return False
    length = int(message[1])
    debug("[ls] Server connected!  Length is %d" %(length))
    # Receive the data
    raw_data = recv_block(sock_data, length)
    if raw_data is None:
        pMsg("[ls] Server hung up")
        teardown_data_conn()
        return False
    data = raw_data.decode()
    pMsg("[ls] %s\n%s" %(path, data), end="")
    # Receive 520 (Success!)
    message = receive_msg(sock_conn)
    if message is None:
        pMsg("[ls] Connection closed by remote host")
        teardown_data_conn()
        return False
    elif message[0] != "520":
        pMsg("[ls] Transfer not successful")
        teardown_data_conn()
        return False
    # TODO: ASCII art of success kid
    # Close stuff
    teardown_data_conn()
    return True
