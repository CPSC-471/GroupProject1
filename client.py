import socket
import sys
from functions import *

# Client code
from socket import *


def listen(server_port):
    new_port = server_port + 1
    # Create a TCP socket
    my_socket = socket(AF_INET, SOCK_STREAM)

    # Bind the socket to the port
    my_socket.bind(('', new_port))

    # Start listening for incoming connections
    my_socket.listen(1)
    my_socket.send(new_port)


def connect(port):
    # Name and port number of the server to # which want to connect .
    server_name = '127.0.0.1'
    server_port = port

    # Create a socket
    client_socket = socket(AF_INET, SOCK_STREAM)

    # Connect to the server
    client_socket.connect((server_name, server_port))

    return client_socket


def get_data(my_socket):
    # get data from user
    global file_name
    x = input('>ftp ')
    b = x.split(" ")
    cmd = b[0]

    while cmd != 'quit':
        if len(b) == 1:
            cmd = b[0]
        else:
            cmd = b[0]
            file_name = b[1]

        # call appropriate function
        if cmd == 'ls':
            # list files on server
            transfer(cmd, my_socket)
            ls_output = my_socket.recv(1024)
            print(ls_output)

        elif cmd == 'put':
            # call put function
            transfer(cmd, my_socket)
            transfer(file_name, my_socket)
            put(file_name, my_socket)

        elif cmd == 'get':
            # call get function
            get()

        elif cmd == 'quit':
            # quit program
            quit()

        else:
            # print menu options
            other()

        x = input('>ftp ')
        b = x.split(" ")
        cmd = b[0]


def main():
    # Command line checks 
    if len(sys.argv) < 2:
        print("USAGE python " + sys.argv[0] + " <Port Number to connect to>")
        sys.exit(1)

    server_port = int(sys.argv[1])

    my_socket = connect(server_port)
    get_data(my_socket)


if __name__ == '__main__':
    main()
