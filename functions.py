def put(file_name, my_socket):
    # Open the file
    file_obj = open(file_name, "r")

    # Keep sending until all is sent
    while True:

        # Read 65536 bytes of data
        file_data = file_obj.read(65536)

        # Make sure we did not hit EOF
        if file_data:

            # Get the size of the data read and convert it to string
            data_size_str = str(len(file_data))

            # Prepend 0's to the size string until the size is 10 bytes
            while len(data_size_str) < 10:
                data_size_str = "0" + data_size_str

            # Prepend the size of the data to the file data.
            file_data = data_size_str + file_data

            # The number of bytes sent
            num_sent = 0

            # Send the data!
            while len(file_data) > num_sent:
                num_sent += my_socket.send(file_data[num_sent:])

        # We are done
        else:
            break

    # Close the file
    file_obj.close()


def get():
    print("I'll get it")


def transfer(info, my_socket):
    data = info
    bytes_sent = 0

    # Keep sending bytes until all bytes are sent
    while bytes_sent != len(data):
        # Send that string !
        bytes_sent += my_socket.send(data[bytes_sent:])


def quit():
    print('quit')


def other():
    print('Wrong input. The following commands are available')
    print('put + filename')
    print('get + filename')
    print('ls - prints out files on server')
    print('quit - exits program')


def recv_all(sock, num_bytes):
    # The buffer
    recv_buff = ''

    # Keep receiving till all is received
    while len(recv_buff) < num_bytes:

        # Attempt to receive bytes
        tmp_buff = sock.recv(num_bytes)

        # The other side has closed the socket
        if not tmp_buff:
            break

        # Add the received bytes to the buffer
        recv_buff += tmp_buff

    return recv_buff
