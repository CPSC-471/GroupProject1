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
    abort(usage.message)
usage.message = """Usage:
    server.py <PORT_NUM>
    server.py <IP> <PORT_NUM>
"""

# Send data (bytes) across socketData to data_ip:data_port
def send_data(data_ip, data_port, data):
    global socketData
    # Connect to the client's data socket
    socketData = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pMsg("**** Attempting to connect to %s:%d" %(data_ip, data_port))
    socketData.connect((data_ip, data_port))
    pMsg("**** Success!")
    # Send 510 with data length
    send_msg(socketClient, MSG_510 % (len(data)))
    # Send data
    socketData.sendall(data)
    socketData.close()

# Check the path to see if it is under PWD
def check_path(path):
    pwd = posixpath.abspath(os.getcwd()) + "/"
    apath = posixpath.abspath(path) + "/"
    return apath.find(pwd) == 0

# Check the file to see if it is under PWD
def check_file(filename):
    pwd = posixpath.abspath(os.getcwd()) + "/"
    apath = posixpath.abspath(filename)
    if (apath.find(pwd) == 0):
        # The file is under PWD.  Check to make sure it is a file
        return posixpath.isfile(apath)
    else:
        # The file is not under PWD.
        return False

# PUT command
# params is the tuple of parameters passed in the 200 MSG
# data_ip is the IP address of the client's data connection
def put(params, data_ip):
    global socketData
    if len(params) < 5:
        send_msg(socketClient, MSG_800)
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
        send_msg(socketClient, MSG_290 %(path))
        socketData.close()
        return False
    # Open the file
    try:
        fd = open(path, "wb")
        # Send 510 with data length
        send_msg(socketClient, MSG_510 % (-1))
        bytesrecv = 0
        while bytesrecv < length:
            length_block = min(length - bytesrecv, 4096)
            pMsg("*put:  Receiving block...")
            block = recv_block(socketData, length_block)
            if block is None:
                # Client hung up
                send_msg(socketClient, MSG_590)
                socketData.close()
                return False
            fd.write(block)
            bytesrecv += length_block
        fd.close()
    except(OSError):
        # Permission problems
        send_msg(socketClient, MSG_290)
        socketData.close()
        return False
    # Send a 520 Success
    send_msg(socketClient, MSG_520)
    socketData.close()
    return True

# LS command
# params is the tuple of parameters passed in the 300 MSG
# data_ip is the IP address of the client's data connection
def ls(params, data_ip):
    if len(params) < 4:
        send_msg(socketClient, MSG_800)
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
        # Send a 520 Success
        send_msg(socketClient, MSG_520)
        return True
    else:
        # Don't list the path.  It's not under PWD
        send_data(data_ip, data_port, "Permission denied!\n".encode())
        send_msg(socketClient, MSG_390 %(path))
        return False

# GET command
def get(params, data_ip):
    global socketData
    if len(params) < 4:
        send_msg(socketClient, MSG_800)
        return False
    data_port = int(params[2])
    filename = params[3]
    if check_file(filename):
        pMsg("Your file has been found")
        fo = open(filename, mode='rb')
        filesize = os.stat(filename).st_size
        # MAX_BYTES should be used here instead of 512
        bytes_read = fo.read(512)
        # Connect to the client's data socket
        socketData = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pMsg("SendingData: Attempting to connect to %s:%d" %(data_ip, data_port))
        socketData.connect((data_ip, data_port))
        pMsg("SendingData: Success!")
        # Send 510 with data length
        send_msg(socketClient, MSG_510 % filesize)
        bytes_sent = 0
        while (bytes_sent < filesize):
            # Send data
            socketData.sendall(bytes_read)
            bytes_sent += len(bytes_read)
            bytes_read = fo.read(512)
        # Send a 520 Success
        send_msg(socketClient, MSG_520)
        socketData.close()
        return True
    else:
        pMsg("*get:  Not a file, or you're not allowed to look in this path")
        send_data(data_ip, data_port, "".encode())
        send_msg(socketClient, MSG_190 %(filename))
        return False

def handle_session(addr):
    pMsg("*SessionHandler:  Handling connection from %s:%d" %(addr[0], addr[1]))
    while True:
        message = recv_msg(socketClient)
        if message is None or len(message) < 1:
            # Gracefully terminate
            socketClient.close()
            break
        elif message[0] == "200":
            # PUT
            put(message, addr[0])
        elif message[0] == "300":
            # LS
            ls(message, addr[0])
        elif message[0] == "800":
            # What you say!!
            pass
        elif message[0] == "900":
            # BYE message.  Quit.
            socketClient.close()
            break
        elif message[0] == "100":
            # GET
            get(message, addr[0])
        else:
            # Send the 800 response (What you say!!)
            send_msg(socketClient, MSG_800)

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
            pMsg("**** Forking child PID %d" %(pid_child))

# Clean things up before terminating
def shutdown(kill_children=False):
    pMsg("**** Shutting down...")
    if isProcess:
        if not socketClient is None: socketClient.close()
        if not socketData is None: socketData.close()
    else:
        if(kill_children):
            pMsg("**** Killing child processes")
            # Turn off child reaping b/c we do it here.
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
            pMsg("**** clearing PID %d" %(pid))
        except(ChildProcessError):
            break;
signal.signal(signal.SIGTERM, handle_kill)
signal.signal(signal.SIGQUIT, handle_kill)
signal.signal(signal.SIGHUP, handle_kill)
signal.signal(signal.SIGCHLD, reap_children)

if __name__ == "__main__":
    try: main()
    except(KeyboardInterrupt):
        # KeyboardInterrupt exits normally
        # The KeyboardInterrupt propagates to all children
        shutdown(kill_children=False)
    except:
        # Everything else is an error and should print a stackdump
        # (Except for sys.exit(0), which also dumps control here)
        shutdown(kill_children=True)
        raise
