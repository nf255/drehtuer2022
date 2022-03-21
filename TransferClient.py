import socket
from tkinter import *
import matplotlib.pyplot as plt
import numpy as np


# Dokumente:
#
# S:\Entwicklung\Allgemein\Datenblätter\Kartentechnik\Kathrein\Programmierung\RRU4 API and Demo V2.56.00\API\Headers
# S:\Entwicklung\Allgemein\Datenblätter\Kartentechnik\Kathrein\Programmierung


def main():
    root.mainloop()


def clickConnect(reader):
    global s
    s = socket.socket()
    try:
        s.connect((reader, 4007))
    except:
        connection_status_label.config(text="Connection failed!", fg='#ff0000')
    else:
        connection_status_label.config(text="Connected to " + reader + "!", fg='#00db07')
        disconnect_button.config(state=NORMAL)
        button_SyncGetEPCs.config(state=NORMAL)


def SyncGetEPCs():
    # enc = [0xaa, 0xbb, 0x01, 0x01, 0x19, 0x00, 0x17, 0xaa, 0xcc] # Extended Result Flag
    for i in range(24, 137):
        enc = [0xaa, 0xbb, 0x01, 0x01, 0x06, 0x00, 0x04, i, 0xaa, 0xcc]  # SetPortPower
        message = bytes(enc)
        s.send(message)
        placeholder = s.recv(buffer)
        enc = [0xaa, 0xbb, 0x01, 0x01, 0x01, 0x01, 0xaa, 0xcc]  # SyncGetEPCs
        message = bytes(enc)
        s.send(message)
        response = s.recv(buffer)
        output_data = createResponseOutput(response)
        # output_data=[{"type": "tag", "time": 55, "rssi": 67, "epc": 243556},
        #             {"type": "tag", "time": 65, "rssi": 87, "epc": 92834728}]
        x_plot = np.array([])
        y_plot = np.array([])
        label_plot = np.array([]).astype('int64')
        for tag in output_data:
            if tag["type"] == "tag":
                x_plot = np.append(x_plot, i / 4)
                y_plot = np.append(y_plot, tag["rssi"])
        plt.plot(x_plot, y_plot, marker='o')
    plt.xlabel("Port Power in dBm")
    plt.ylabel("RSSI Value")
    plt.show()


def createResponseOutput(response):
    handover = [hex(int(i)) for i in response]
    handover = handover[4:]
    command_id = hex(((int(handover[1], base=16) << 8) ^ (2 ** 15)) + int(handover[0], base=16))
    command_data = handover[2:]
    command_res_dict = {
        "0x101": rSyncGetEPCs
    }
    r_command = command_res_dict.get(command_id)
    output = r_command(command_data)
    return output


def rSyncGetEPCs(c_data):
    tag_list = []
    info = {"type": "info", "command": "SyncGetEPCs"}
    if c_data[0] == "0x0":
        info["error"] = "none"
    elif c_data[0] == "0xA":
        info["error"] = "no_tag"
    else:
        info["error"] = c_data[0]
    del c_data[0]
    tag_list.append(info)
    e_flag = int(c_data[0], base=16)
    if info["error"] == "none":
        while True:
            extended_result = {"type": "tag"}
            if e_flag == (e_flag | 2 ** 0):
                extended_result["port"] = c_data[1][-1]
                del c_data[1]
            if e_flag == (e_flag | 2 ** 1):
                extended_result["rssi"] = int(c_data[1], base=16)
                del c_data[1]
            if e_flag == (e_flag | 2 ** 2):
                extended_result["time"] = int(c_data[1], base=16) + (int(c_data[2], base=16) << 8) + (
                        int(c_data[3], base=16) << 16) + (int(c_data[4], base=16) << 24)
                del c_data[1:5]
            if e_flag == (e_flag | 2 ** 3):
                extended_result["pc"] = int(c_data[1], base=16) + (int(c_data[2], base=16) << 8) + (
                        int(c_data[3], base=16) << 16) + (int(c_data[4], base=16) << 24) + (
                                                int(c_data[5], base=16) << 32) + (int(c_data[6], base=16) << 40)
                del c_data[1:7]
            if e_flag == (e_flag | 2 ** 4):
                extended_result["frequency"] = int(c_data[1], base=16) + (int(c_data[2], base=16) << 8) + (
                        int(c_data[3], base=16) << 16)
                del c_data[1:4]
                extended_result["phase"] = int(c_data[1], base=16) + (int(c_data[2], base=16) << 8)
                del c_data[1:3]
            epc_bytes = int(c_data[1], base=16) * 2
            del c_data[1]
            epc = 0
            for i in range(1, epc_bytes + 1):
                epc = epc + (int(c_data[(epc_bytes - (i - 1))], base=16) << ((i - 1) * 8))
            del c_data[1:(epc_bytes + 1)]
            extended_result["epc"] = hex(epc)
            tag_list.append(extended_result)
            if c_data[1] == "0xaa" and c_data[2] == "0xcc":
                break
    return tag_list


root = Tk()
root.title("KBRP V2 Test")

s = socket.socket()
buffer = 16384

# Creating a Label Widget and a button
reader_ip_label = Label(root, text="Reader IP:")
reader_ip_entry = Entry(root, width=20)
connect_button = Button(root, text="Connect",
                        command=lambda: [clickConnect(reader_ip_entry.get()),
                                         connect_button.config(state=DISABLED)])
disconnect_button = Button(root, text="Disconnect",
                           command=lambda: [s.close(),
                                            connection_status_label.config(text="Disconnected!", fg='#ff0000'),
                                            disconnect_button.config(state=DISABLED),
                                            connect_button.config(state=NORMAL),
                                            button_SyncGetEPCs.config(state=DISABLED)],
                           state=DISABLED)
connection_status_label = Label(root, text="")
button_SyncGetEPCs = Button(root, text="SyncGetEPCs", command=SyncGetEPCs, state=DISABLED)
label_SyncGetEPCs = Label(root, text="")

# Shoving elements onto the screen
reader_ip_label.grid(row=0, column=0, padx=10, pady=10)
reader_ip_entry.grid(row=0, column=1, padx=10, pady=10)
reader_ip_entry.insert(0, "192.168.3.46")
connect_button.grid(row=0, column=2, padx=10, pady=10)
disconnect_button.grid(row=0, column=3, padx=10, pady=10)
connection_status_label.grid(row=1, column=0, columnspan=4)
button_SyncGetEPCs.grid(row=2, column=0, padx=10, pady=10)
label_SyncGetEPCs.grid(row=3, column=0, columnspan=4)

if __name__ == '__main__':
    main()
