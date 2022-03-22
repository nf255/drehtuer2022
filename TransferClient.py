import socket
from tkinter import *
import matplotlib.pyplot as plt
import numpy as np
import time


# Notes:
#
# S:\Entwicklung\Allgemein\Datenblätter\Kartentechnik\Kathrein\Programmierung\RRU4 API and Demo V2.56.00\API\Headers
# S:\Entwicklung\Allgemein\Datenblätter\Kartentechnik\Kathrein\Programmierung
# terminal: auto-py-to-exe


def main():
    reader_ip_label.grid(row=0, column=0, padx=8, pady=8)
    reader_ip_entry.grid(row=0, column=1, padx=8, pady=8)
    reader_ip_entry.insert(0, "192.168.3.46")
    connect_button.grid(row=0, column=2, padx=8, pady=8)
    disconnect_button.grid(row=0, column=3, padx=8, pady=8)
    connection_status_label.grid(row=1, column=0, columnspan=4)
    button_SyncGetEPCs_increasing_power.grid(row=2, column=0, padx=8, pady=8)
    button_SyncGetEPCs_timer.grid(row=3, column=0, rowspan=2, padx=8, pady=8)
    timer_time_entry_label.grid(row=3, column=1, padx=8, pady=8)
    timer_time_entry.grid(row=4, column=1, padx=8, pady=8)
    timer_time_entry.insert(0, 10)
    timer_power_entry_label.grid(row=3, column=2, padx=8, pady=8)
    timer_power_entry.grid(row=4, column=2, padx=8, pady=8)
    timer_power_entry.insert(0, 20.0)
    timer_alert_label.grid(row=5, column=0, columnspan=4, padx=8, pady=8)
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
        connect_button.config(state=DISABLED)
        disconnect_button.config(state=NORMAL)
        button_SyncGetEPCs_increasing_power.config(state=NORMAL)
        button_SyncGetEPCs_timer.config(state=NORMAL)


def SyncGetEPCs(mode, timer_time, timer_power):
    # enc = [0xaa, 0xbb, 0x01, 0x01, 0x19, 0x00, 0x17, 0xaa, 0xcc] # Extended Result Flag
    if mode == "power":
        plot_data = {}
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
            for tag in output_data:
                if tag["type"] == "tag":
                    if tag["epc"] not in plot_data:
                        plot_data[tag["epc"]] = np.zeros((2, 113))
                        plot_data[tag["epc"]][0] = [power / 4 for power in range(24, 137)]
                    plot_data[tag["epc"]][1][i - 24] = tag["rssi"]
        for key, value in plot_data.items():
            plt.plot(value[0], value[1], label=key[20:])
        plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.xlabel("Port Power in dBm")
        plt.ylabel("RSSI Value")
        plt.title("Tag detection from 6 dBm to 34 dBm")
        plt.tight_layout()
        plt.show()

    elif mode == "timer":
        if 6 <= timer_power <= 34:
            plot_data = {}
            enc = [0xaa, 0xbb, 0x01, 0x01, 0x06, 0x00, 0x04, int(timer_power * 4), 0xaa, 0xcc]  # SetPortPower
            message = bytes(enc)
            s.send(message)
            placeholder = s.recv(buffer)
            process_time = time.perf_counter()
            while time.perf_counter() - process_time < timer_time:
                enc = [0xaa, 0xbb, 0x01, 0x01, 0x01, 0x01, 0xaa, 0xcc]  # SyncGetEPCs
                message = bytes(enc)
                s.send(message)
                response = s.recv(buffer)
                output_data = createResponseOutput(response)
                epc_out_list = []
                for tag in output_data:
                    if tag["type"] == "tag":
                        if tag["epc"] not in plot_data:
                            plot_data[tag["epc"]] = [[], []]
                        plot_data[tag["epc"]][0].append(time.perf_counter() - process_time)
                        plot_data[tag["epc"]][1].append(tag["rssi"])
                        epc_out_list.append(tag["epc"])
                for epc in plot_data:
                    if epc not in epc_out_list:
                        plot_data[epc][0].append(time.perf_counter() - process_time)
                        plot_data[epc][1].append(0)
                time.sleep(0.1)
            for key, value in plot_data.items():
                plt.plot(value[0], value[1], label=key[20:])
            plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
            plt.xlabel("Time in Seconds")
            plt.ylabel("RSSI Value")
            plt.title("Tag detection for " + str(timer_time) + " Seconds with " + str(timer_power) + " dBm")
            plt.tight_layout()
            plt.show()
        else:
            timer_alert_label.config(text="6 dBm <= Power <= 34 dBm!")


def createResponseOutput(response):
    handover = ["0x"+hex(int(i))[2:].zfill(2) for i in response]
    for count, value in enumerate(handover):
        if value == "0xaa" and handover[count+1] == "0xaa":
            del handover[count]
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
    if c_data[0] == "0x00":
        info["error"] = "none"
    elif c_data[0] == "0x0A":
        info["error"] = "no_tag"
    else:
        info["error"] = c_data[0]
    del c_data[0]
    tag_list.append(info)
    e_flag = int(c_data[0], base=16)
    if info["error"] == "none":
        while True:
            if c_data[1] == "0xaa" and c_data[2] == "0xcc":
                break
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
            epc = ""
            for i in range(1, epc_bytes + 1):
                epc = str(c_data[i][2:]) + epc
            del c_data[1:(epc_bytes + 1)]
            extended_result["epc"] = epc
            tag_list.append(extended_result)
    return tag_list


root = Tk()
root.title("KBRP V2 Test")

s = socket.socket()
buffer = 16384

# Creating a Label Widget and a button
reader_ip_label = Label(root, text="Reader IP:")
reader_ip_entry = Entry(root, width=20)
connect_button = Button(root, text="Connect", command=lambda: clickConnect(reader_ip_entry.get()))
disconnect_button = Button(root,
                           text="Disconnect",
                           command=lambda: [s.close(),
                                            connection_status_label.config(text="Disconnected!", fg='#ff0000'),
                                            disconnect_button.config(state=DISABLED),
                                            connect_button.config(state=NORMAL),
                                            button_SyncGetEPCs_increasing_power.config(state=DISABLED),
                                            button_SyncGetEPCs_timer.config(state=DISABLED)],
                           state=DISABLED)
connection_status_label = Label(root, text="")
button_SyncGetEPCs_increasing_power = Button(root,
                                             text="Increasing Power",
                                             command=lambda: SyncGetEPCs("power", 0, 0),
                                             state=DISABLED)
button_SyncGetEPCs_timer = Button(root,
                                  text="Timer",
                                  command=lambda: SyncGetEPCs("timer",
                                                              int(timer_time_entry.get()),
                                                              round(float(timer_power_entry.get()) * 4) / 4),
                                  state=DISABLED)
timer_time_entry_label = Label(root, text="Time (s):")
timer_time_entry = Entry(root, width=8)
timer_power_entry_label = Label(root, text="Power (dBm):")
timer_power_entry = Entry(root, width=8)
timer_alert_label = Label(root, text="", fg='#ff0000')


if __name__ == '__main__':
    main()
