# *******************************************************************
# Server Side
#   - Server Side goes here
# -------------------------------------------------------------------
# Author: Jeffrey Lo, Mike Souchitto, Joseph Chau
# *******************************************************************

from commonFuncs import *
import sys
import time
import os
import posixpath
import signal
import socket
import subprocess

# Max Buffer Size
MAX_BYTES = 512

# Default IPs and ports to bind to
serverIP = "localhost"
serverPort = 1234

# Sockets
socketWelcome = None
socketClient = None
socketData = None

isProcess = False
connectProcess = set()


def usage():
    usage.message = """Usage:
        server.py <PORT_NUM>
        server.py <IP> <PORT_NUM>
    """
    quit(usage.message)


# Send data (bytes) across socketData to data_ip:data_port
def send_data(data_ip, data_port, data):
    global socketData
    # Connect to the client's data socket
    socketData = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pMsg("**** Attempting to connect to %s:%d" %(data_ip, data_port))
    socketData.connect((data_ip, data_port))
    pMsg("**** Success!")
    # Send 510 with data length
    send_msg(socketClient, CODE_5010 % (len(data)))
    # Send data
    socketData.sendall(data)
    socketData.close()

# Check the file if valid
def check_file(filename):
    getPath = posixpath.abspath(os.getcwd()) + "/"
    tempPath = posixpath.abspath(filename)
    if (tempPath.find(getPath) == 0):
        # The file is under getPath.  Check to make sure it is a file
        return posixpath.isfile(tempPath)
    else:
        # The file is not under getPath.
        return False

# Check the path to see if it is under PWD
def check_path(path):
    pwd = posixpath.abspath(os.getcwd()) + "/"
    tempPath = posixpath.abspath(path) + "/"
    return tempPath.find(pwd) == 0

# PUT command
def put(params, data_ip):
    global socketData
    if len(params) < 5:
        send_msg(socketClient, CODE_4000)
        return False
    data_port = int(params[2])
    length = int(params[3])
    path = params[4]
    # Connect to the client's data socket
    socketData = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pMsg("*put:  Attempting to connect to %s:%d" %(data_ip, data_port))
    socketData.connect((data_ip, data_port))
    pMsg("*put:  Success!")
    if not check_path(path):
        # Don't write it!  It's not under PWD
        send_msg(socketClient, CODE_2090 %(path))
        socketData.close()
        return False
    # Open the file
    try:
        fd = open(path, "wb")
        # Send 510 with data length
        send_msg(socketClient, CODE_5010 % (-1))
        bytesrecv = 0
        while bytesrecv < length:
            length_block = min(length - bytesrecv, 4096)
            pMsg("*put:  Receiving block...")
            block = recv_block(socketData, length_block)
            if block is None:
                # Client hung up
                send_msg(socketClient, CODE_5090)
                socketData.close()
                return False
            fd.write(block)
            bytesrecv += length_block
        fd.close()
    except(OSError):
        # Permission problems
        send_msg(socketClient, CODE_2090)
        socketData.close()
        return False
    # Send a 520 Success
    send_msg(socketClient, CODE_5020)
    socketData.close()
    return True

# LS command
def ls(params, data_ip):
    if len(params) < 4:
        send_msg(socketClient, CODE_4000)
        return False
    data_port = int(params[2])
    path = params[3]
    # Check the path
    if check_path(path):
        # Run ls -la
        ls_data = subprocess.Popen(
                ["ls", "-al", "--", path],
                universal_newlines=False,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE).stdout.read()
        send_data(data_ip, data_port, ls_data)
        send_msg(socketClient, CODE_5020)
        return True
    else:
        send_data(data_ip, data_port, "Access Denied - Check Permissions or password locked file\n".encode())
        send_msg(socketClient, CODE_3090 %(path))
        return False

# GET command
def get(params, data_ip):
    global socketData
    if len(params) < 4:
        send_msg(socketClient, CODE_4000)
        return False
    data_port = int(params[2])
    filename = params[3]
    if check_file(filename):
        pMsg("Your file has been found")
        fo = open(filename, mode='rb')
        filesize = os.stat(filename).st_size
        bytes_read = fo.read(MAX_BYTES)
        # Connect to the client's data socket
        socketData = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pMsg("SendingData: Attempting to connect to %s:%d" %(data_ip, data_port))
        socketData.connect((data_ip, data_port))
        pMsg("SendingData: Success!")
        # Send 5010 with data length
        send_msg(socketClient, CODE_5010 % filesize)
        bytes_sent = 0
        while (bytes_sent < filesize):
            # Send data
            socketData.sendall(bytes_read)
            bytes_sent += len(bytes_read)
            bytes_read = fo.read(MAX_BYTES)
        # Send a 5020 Success
        send_msg(socketClient, CODE_5020)
        socketData.close()
        return True
    else:
        pMsg("*get:  Not a file, denied file access")
        send_data(data_ip, data_port, "".encode())
        send_msg(socketClient, CODE_1090 %(filename))
        return False

def handle_session(addr):
    pMsg("*SessionHandler:  Handling connection from %s:%d" %(addr[0], addr[1]))
    while True:
        message = receive_msg(socketClient)
        if message is None or len(message) < 1:
            socketClient.close()
            break
        elif message[0] == "2000":
            # PUT
            put(message, addr[0])
        elif message[0] == "3000":
            # LS
            ls(message, addr[0])
        elif message[0] == "4000":
            # What you say!!
            pass
        elif message[0] == "9000":
            # BYE message.  Quit.
            socketClient.close()
            break
        elif message[0] == "1000":
            # GET
            get(message, addr[0])
        else:
            send_msg(socketClient, CODE_4000)

def main():
    global socketWelcome, socketClient, serverIP, serverPort, isProcess, connectProcess

    # Parse CLI parameters
    if len(sys.argv) < 2: usage()
    elif len(sys.argv) == 2:
        serverPort = int(sys.argv[1])

    # Create the welcome socket
    socketWelcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketWelcome.bind((serverIP, serverPort))
    socketWelcome.listen(1)

    pMsg("**** Listening on %s:%d" %(serverIP, serverPort))

    # Accept connections
    while True:
        pMsg("**** Awaiting connection...")
        try:
            socketClient, addr = socketWelcome.accept()
        except (InterruptedError):
            continue
        pMsg("**** Accepted connection from %s:%d" %(addr[0], addr[1]))
        # This is where you and the client talk
        pid_child = os.fork()
        if pid_child == 0:
            # Child
            isProcess = True
            connectProcess = set()
            handle_session(addr)
            sys.exit(0)
        else:
            # Parent
            connectProcess.add(pid_child)
            #pMsg("**** Forking child PID %d" %(pid_child))

# Clean things up before terminating
def shutdown(kill_children=False):
    pMsg("**** Shutting down...")
    if isProcess:
        if not socketClient is None: socketClient.close()
        if not socketData is None: socketData.close()
    else:
        if(kill_children):
            pMsg("**** Killing child processes")
            signal.signal(signal.SIGCHLD, signal.SIG_DFL)
            for pid in connectProcess:
                pMsg("**** Sending SIGTERM to %d" %(pid))
                os.kill(pid, signal.SIGTERM)
                os.waitpid(pid, 0)
        if not socketWelcome is None: socketWelcome.close()

# Signal handlers
def handle_kill(sig, frame):
    pMsg("**** Received signal %d." %(sig))
    # This will actually raise an exception, which throws control
    # back to shutdown (see the end of the file).
    sys.exit(0)

def reap_children(sig, frame):
    while True:
        try:
            status = os.waitpid(-1, os.WNOHANG)
            pid = status[0]
            if pid <= 0:
                break;
            connectProcess.discard(pid)
            #pMsg("**** clearing PID %d" %(pid))
        except(ChildProcessError):
            break;

signal.signal(signal.SIGTERM, handle_kill)
signal.signal(signal.SIGQUIT, handle_kill)
signal.signal(signal.SIGHUP, handle_kill)
signal.signal(signal.SIGCHLD, reap_children)

if __name__ == "__main__":
    try: main()
    except(KeyboardInterrupt):
        shutdown(kill_children=False)
    except:
        shutdown(kill_children=True)
        raise
