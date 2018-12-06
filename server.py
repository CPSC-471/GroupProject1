# Server code
from socket import *
import sys
import subprocess
from functions import*

def main():

    # Command line checks 
    if len(sys.argv) < 2:
        print("USAGE python " + sys.argv[0] + " <Port #>")
        sys.exit(1)

    port = int(sys.argv[1])

    # The port on which to listen
    server_port = port

    # Create a TCP socket
    server_socket = socket(AF_INET,SOCK_STREAM)

    
    # Bind the socket to the port
    server_socket.bind(( '', server_port ))

    # Start listening for incoming connections
    server_socket.listen(1)
    print("Server Socket listening")

    # Forever accept incoming connections
    while 1:
        
        print('Ready to receive')

        # Accept a connection and get client 's socket
        connection_socket , addr = server_socket.accept()

        data = ""

        # accept commands from client forever
        while not len(data) == 40:
            data = ""

            # Receive whatever the newly connected client has to send
            tmp_buff = connection_socket.recv(40)

            # The other side unexpectedly closed it 's socket
            if not tmp_buff :
                break

            # Save the data
            data += tmp_buff

            print(data)

            # do commands

            if data == 'ls':
                ls_output = subprocess.Popen(['ls','-1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
                output = ls_output.stdout.read()
                connection_socket.send(output)

            elif data == 'put':
                file_name = connection_socket.recv(40)
                print(file_name)
                
                # Receive the first 10 bytes indicating the size of the file
                file_size_buff = recv_all(connection_socket, 10)
                
                # Get the file size
                file_size = int(file_size_buff)

                print("The file size is ", file_size)

                # Get the file data
                file_data = recv_all(connection_socket, file_size)

                print("The file data is: ")
                print(file_data)

                # Copy data to a new file
                o = open('s.txt', 'w+')
                o.write(file_data)
                o.close()

        # Close the socket
        connection_socket.close()

if __name__ == '__main__':
    main()

