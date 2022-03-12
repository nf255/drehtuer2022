import socket

# Dokumente:
#
# S:\Entwicklung\Allgemein\Datenblätter\Kartentechnik\Kathrein\Programmierung\RRU4 API and Demo V2.56.00\API\Headers
# S:\Entwicklung\Allgemein\Datenblätter\Kartentechnik\Kathrein\Programmierung


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
            command_id, command_data = createResponseOutput(response)
            print(f"Command {command_id} returned {command_data}")

            break
    except:
        print("Connection Failed!")
    finally:
        s.close()
        print("Disconnected!")


def createResponseOutput(response):
    handover = [hex(int(i)) for i in response]
    for i in range(0, 4, 1):
        handover.pop(0)
    handover.pop(-1)
    handover.pop(-1)
    command_id = hex(((int(handover[1], base=16) << 8) ^ (2 ** 15)) + int(handover[0], base=16))
    command_data = handover[2:]
    
    command_dict = {
        "0x101": rSyncGetEPC
    }
    
    rCommand = command_dict.get(command_id)
    output = rCommand(command_data)
    return output


def rSyncGetEPC(command_data):
    return command_data



if __name__ == '__main__':
    main()
