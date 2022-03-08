import socket
import os


def main():
    host = "0.0.0.0"
    sep = "#SEP#"
    port = 1155
    buffer = 1024

    s = socket.socket()
    s.bind((host, port))
    s.listen(1)
    print("Server open...")
    client_socket, address = s.accept()
    print(f"{address} connected...")
    file, file_size = client_socket.recv(buffer).decode().split(sep)

    file_name = os.path.basename(file)
    file_size = int(file_size)
    with open(file_name, "wb") as f:
        bytes_recv = client_socket.recv(buffer)
        while bytes_recv:
            f.write(bytes_recv)
            bytes_recv = client_socket.recv(buffer)
    client_socket.close()
    s.close()


if __name__ == '__main__':
    main()
