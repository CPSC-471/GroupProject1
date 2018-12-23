# *******************************************************************
# Client Side
# 	- Client related code found here
# -------------------------------------------------------------------
# Author: Jeffrey Lo, Mike Souchitto, Joseph Chau
# *******************************************************************
from commonFuncs import*
#from CliCommandFunctions import*
import socket
import os
import sys
import time
import subprocess
import signal

# Max Buffer Size
MAX_BYTES = 512

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
	howUse.message = """How to Use Client: client.py <serverIP> <serverPort>"""
	quit(howUse.message)

def helpPrompt():
	helpPrompt.message = """
	Commands:
		get <filename>
		put <filename>
		ls <path>
		help
		quit"""
	pMsg(helpPrompt.message)

def terminate():
	pMsg("Goodbye - Disconnecting")
	send_msg(sock_conn, CODE_9000)

def setup_conn():
	sock_welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_welcome.bind((clientIP, 0))
	sock_welcome.listen(1)
	addr = sock_welcome.getsockname()
	#pMsg("**setup_conn Listening on %s:%d" %(addr[0], addr[1]))
	return sock_welcome

def close_conn():
	global sock_data_welcome, sock_data
	if not sock_data is None:
		sock_data.close()
		sock_data = None
	if not sock_data_welcome is None:
		sock_data_welcome.close()
		sock_data_welcome = None

# GET
def get(filename):
	global sock_data_welcome, sock_data
	# ephemeral port
	sock_data_welcome = setup_conn()
	port = sock_data_welcome.getsockname()[1]
	# Send 1000 message with port number
	send_msg(sock_conn, CODE_1000 %(port, filename))
	# Accept server
	pMsg("*get: Waiting for server to connect")
	sock_data, addr = sock_data_welcome.accept()
	# Wait for 5010 with size
	message = receive_msg(sock_conn)
	if message is None:
		pMsg("*get: Connection closed by remote host")
		close_conn()
		return False
	elif message[0] != "5010" or len(message) < 2:
		close_conn()
		return False
	length = int(message[1])
	pMsg("*get: Server connected!  Length is %d" %(length))
	bytes_received = 0
	try:
		# Write file to the current directory, even if it is in a server subdir
		short_filename = os.path.split(filename)[1]
		fo = open(short_filename, mode='wb')
		while (bytes_received < length):
			raw_data = recv_block(sock_data, min(MAX_BYTES, length - bytes_received))
			if raw_data is None:
				pMsg("*get: Server hung up")
				close_conn()
				return False
			bytes_received += len(raw_data)
			fo.write(raw_data)
		fo.close()
	except(OSError):
		pMsg("*get: Cannot open file")
		close_conn()
		return False
	# Receive 5020 (Success!)
	message = receive_msg(sock_conn)
	if message is None:
		pMsg("*get: Connection closed by remote host")
		close_conn()
		return False
	elif message[0] != "5020":
		pMsg("*get: Transfer not successful")
		close_conn()
		return False
	# Close stuff
	close_conn()
	return True

# PUT
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
	sock_data_welcome = setup_conn()
	port = sock_data_welcome.getsockname()[1]
	# Send 2000 message with port number
	send_msg(sock_conn, CODE_2000 %(port, length, filename))
	# Accept server connection
	pMsg("*put: Waiting for server to connect")
	sock_data, addr = sock_data_welcome.accept()
	# Wait for 5010
	message = receive_msg(sock_conn)
	if message is None:
		pMsg("*put: Connection closed by remote host")
		close_conn()
		return False
	elif message[0] != "5010" or len(message) < 2:
		close_conn()
		return False
	pMsg("*put: Server connected!  Sending %d bytes" %(length))
	# Transmit the data
	try:
		fd = open(path, "rb")
		bytessent = 0
		while bytessent < length:
			raw_data = fd.read(4096)
			#pMsg("*put: Sending block...")
			sock_data.sendall(raw_data)
			bytessent += len(raw_data)
		fd.close()
	except(OSError):
		pMsg("*put: Cannot open file")
		close_conn()
		return False
	# Receive 5020 (Success!)
	message = receive_msg(sock_conn)
	if message is None:
		pMsg("*put: Connection closed by remote host")
		close_conn()
		return False
	elif message[0] != "5020":
		pMsg("*put: Transfer not successful")
		close_conn()
		return False
	# TODO: ASCII art of success kid
	# Close stuff
	close_conn()
	return True

# LS
def ls(path):
	global sock_data_welcome, sock_data
	# Allocate ephemeral port
	sock_data_welcome = setup_conn()
	port = sock_data_welcome.getsockname()[1]
	# Send 300 message with port number
	send_msg(sock_conn, CODE_3000 %(port, path))
	# Accept server connection
	pMsg("*ls:  Waiting for server to connect")
	sock_data, addr = sock_data_welcome.accept()
	# Wait for 5010 with chunk size
	message = receive_msg(sock_conn)
	if message is None:
		pMsg("*ls:  Connection closed by remote host")
		close_conn()
		return False
	elif message[0] != "5010" or len(message) < 2:
		close_conn()
		return False
	length = int(message[1])
	pMsg("*ls:  Server connected!  Length is %d" %(length))
	# Receive the data
	raw_data = recv_block(sock_data, length)
	if raw_data is None:
		pMsg("*ls:  Server hung up")
		close_conn()
		return False
	data = raw_data.decode()
	pMsg("*ls:  %s\n%s" %(path, data), end="")
	# Receive 5020
	message = receive_msg(sock_conn)
	if message is None:
		pMsg("*ls:  Connection closed by remote host")
		close_conn()
		return False
	elif message[0] != "5020":
		pMsg("*ls:  Transfer not successful")
		close_conn()
		return False
	# Close stuff
	close_conn()
	return True

def promptCheck():
	try:
		command_raw = prompt()
	except(EOFError):
		terminate()
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
		helpPrompt()
	elif (command[0].lower() == 'quit' or command[0].lower() == 'q'):
		terminate()
		return False
	else:
		pMsg("INPUT ERROR- No such command")
	return True


def main():
	global serverIP, serverPort, sock_conn

	# Parse CLI parameters
	if len(sys.argv) < 3: howUse()
	serverIP = sys.argv[1]
	serverPort = int(sys.argv[2])

	# Connect to the server
	sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	pMsg("**** Binding  %s:%d" %(serverIP, serverPort))
	sock_conn.connect((serverIP, serverPort))
	pMsg("**** Success")
	while promptCheck(): pass
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
		shutdown()
	except:
		shutdown()
		raise
