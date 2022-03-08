import socket


def main():
    reader = "192.168.3.46"
    port = 4007
    buffer = 16384

    s = socket.socket()
    try:
        s.connect((reader, port))
        while True:
            a = [0xaa, 0xbb, 0x01, 0x01, 0x01, 0x01, 0xaa, 0xcc]
            message = bytes(a)
            s.send(message)

            response = s.recv(buffer)
            b = [hex(int(i)) for i in response]
            print(b)
#            print(repr(b))
            break
    except:
        print("Disconnected!")
    finally:
        s.close()


if __name__ == '__main__':
    main()
