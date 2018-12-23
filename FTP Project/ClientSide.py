# *******************************************************************
# Client Side
# 	- Client related code found here
# -------------------------------------------------------------------
# Author: Jeffrey Lo, Mike Souchitto, Joseph Chau
# *******************************************************************
from commonFuncs import*
from CliCommandFunctions import*
import socket
import os
import sys
import time
import subprocess
import signal

# Server IP and Port
serverIP = "localhost"
serverPort = 1234

# Client IP
clientIP = ""

# Socket
sock_conn = None
sock_data_welcome = None
sock_data = None

def howUse():
	howUse.message = """How to Use Client: client.py <serverIP> <serverPort"""
	quit(howUse.message)

def helpPrompt():
	helpPrompt.message = """Commands:
	    get <filename>
	    put <filename>
	    ls [<path>]
	    help
	    quit"""
    pMsg(helpPrompt.message)

def terminate():
	send_msg(sock_conn, MSG_900)

def setup_conn():
    sock_welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_welcome.bind((clientIP, 0))
    sock_welcome.listen(1)
    addr = sock_welcome.getsockname()
    pMsg("**setup_conn Listening on %s:%d" %(addr[0], addr[1]))
    return sock_welcome

def close_conn():
    global sock_data_welcome, sock_data
    if not sock_data is None:
        sock_data.close()
        sock_data = None
    if not sock_data_welcome is None:
        sock_data_welcome.close()
        sock_data_welcome = None

def promptCheck():
    try:
        command_raw = prompt()
    except(EOFError):
        quit()
        return False
    command = command_raw.strip()
    command = command.split(maxsplit=1)
    if len(command) == 0:
        pass
    elif command[0].lower() == 'ls':
        if len(command) < 2:
            ls("./")
        else:
            ls(command[1])
    elif command[0].lower() == 'get':
        if len(command) < 2:
            pMsg("Get What?")
        else:
            get(command[1])
    elif command[0].lower() == 'put':
        if len(command) < 2:
            pMsg("Put What?")
        else:
            put(command[1])
    elif command[0].lower() == 'help':
        prompt_help()
    elif command[0].lower() == 'quit':
        quit()
        return False
    else:
        # No such command
        pMsg("***PromptError - No such command")
    return True


def main():
    global serverIP, serverPort, sock_conn

    # Parse CLI parameters
    if len(sys.argv) < 3: howUse()
    serverIP = sys.argv[1]
    serverPort = int(sys.argv[2])

    # Connect to the server
    sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pMsg("**** Attempting to bind to %s:%d" %(serverIP, serverPort))
    sock_conn.connect((serverIP, serverPort))
    pMsg("**** Success!")
    while prompt_loop(): pass
    sock_conn.close()

# Clean things up before terminating
def shutdown():
    pMsg("**** Shutting down...")
    if not sock_conn is None: sock_conn.close()
    if not sock_data_welcome is None: sock_data_welcome.close()
    if not sock_data is None: sock_data.close()

# Signal handler
def handle_kill(sig, frame):
    pMsg("**** Received signal %d." %(sig))
    # This will actually raise an exception, which throws control
    # back to shutdown (see the end of the file).
    sys.exit(0)
signal.signal(signal.SIGTERM, handle_kill)
signal.signal(signal.SIGQUIT, handle_kill)
signal.signal(signal.SIGHUP, handle_kill)

if __name__ == "__main__":
    try: main()
    except(KeyboardInterrupt):
        # KeyboardInterrupt exits normally
        # The KeyboardInterrupt propagates to all children
        shutdown()
    except:
        # Everything else is an error and should print a stackdump
        # (Except for sys.exit(0), which also dumps control here)
        shutdown()
        raise
