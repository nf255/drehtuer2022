import socket
from tkinter import *
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
import time
import json


# Notes:
#
# S:\Entwicklung\Allgemein\Datenblätter\Kartentechnik\Kathrein\Programmierung\RRU4 API and Demo V2.56.00\API\Headers
# S:\Entwicklung\Allgemein\Datenblätter\Kartentechnik\Kathrein\Programmierung
# terminal: auto-py-to-exe
# rssiThreshold


def main():
    reader_ip_label.grid(row=0, column=0, padx=8, pady=16)
    reader_ip_entry.grid(row=0, column=1, padx=8, pady=16)
    reader_ip_entry.insert(0, "192.168.3.46")
    connect_button.grid(row=0, column=2, padx=8, pady=16)
    disconnect_button.grid(row=0, column=3, padx=8, pady=16)
    connection_status_label.grid(row=1, column=0, columnspan=4)
    button_SyncGetEPCs_rssi_timer.grid(row=3, column=0, padx=8, pady=8)
    button_SyncGetEPCs_phase_timer.grid(row=4, column=0, padx=8, pady=8)
    button_SyncGetEPCs_ann.grid(row=6, column=3, padx=8, pady=8)
    timer_time_entry_label.grid(row=3, column=1, padx=8, pady=8)
    timer_time_entry.grid(row=4, column=1, padx=8, pady=8)
    timer_time_entry.insert(0, 10)
    timer_power_entry_label.grid(row=3, column=2, padx=8, pady=8)
    timer_power_entry.grid(row=4, column=2, padx=8, pady=8)
    timer_power_entry.insert(0, 30.0)
    timer_rssi_threshold_entry_label.grid(row=3, column=3, padx=8, pady=8)
    timer_rssi_threshold_entry.grid(row=4, column=3, padx=8, pady=8)
    timer_rssi_threshold_entry.insert(0, 50)
    timer_alert_label.grid(row=6, column=1, columnspan=2, padx=8, pady=8)
    button_SyncGetEPCs_increasing_power.grid(row=6, column=0, padx=8, pady=8)
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
        button_SyncGetEPCs_rssi_timer.config(state=NORMAL)
        button_SyncGetEPCs_phase_timer.config(state=NORMAL)
        button_SyncGetEPCs_ann.config(state=NORMAL)


def SyncGetEPCs(mode, value_mode, timer_time, timer_power, timer_threshold):
    try:
        timer_time = int(round(float(timer_time)))
    except:
        timer_alert_label.config(text="Invalid Time Input!")
        return
    try:
        timer_power = round(float(timer_power) * 4) / 4
    except:
        timer_alert_label.config(text="Invalid Power Input!")
        return
    try:
        timer_threshold = int(round(float(timer_threshold)))
    except:
        # timer_alert_label.config(text="Invalid RSSI Input!")
        timer_threshold = 0
    enc = [0xaa, 0xbb, 0x01, 0x01, 0x19, 0x00, 0x17, 0xaa, 0xcc]  # Extended Result Flag
    message = bytes(enc)
    s.send(message)
    placeholder = s.recv(buffer)
    if mode == "power":
        plot_data = {}
        for port_power_value in range(24, 137):
            for port_number in range(1, 5):
                enc = [0xaa, 0xbb, 0x01, 0x01, 0x06, 0x00, port_number, port_power_value, 0xaa, 0xcc]  # SetPortPower
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
                    plot_data[tag["epc"]][1][port_power_value - 24] = tag["rssi"]
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
            for port_number in range(1, 5):
                enc = [0xaa, 0xbb, 0x01, 0x01, 0x06, 0x00, port_number, int(timer_power * 4), 0xaa, 0xcc]  # SetPortPower
                message = bytes(enc)
                s.send(message)
                placeholder = s.recv(buffer)
            loop_counter = 0
            process_time = time.perf_counter()
            while time.perf_counter() - process_time < timer_time:
                while time.perf_counter() - process_time < loop_counter * 0.2:
                    pass
                enc = [0xaa, 0xbb, 0x01, 0x01, 0x01, 0x01, 0xaa, 0xcc]  # SyncGetEPCs
                message = bytes(enc)
                s.send(message)
                response = s.recv(buffer)
                output_data = createResponseOutput(response)
                epc_out_list = []
                for tag in output_data:
                    if tag["type"] == "tag":
                        if tag["epc"] not in plot_data:
                            plot_data[tag["epc"]] = [[step / 5 for step in range(0, (timer_time * 5) + 1)],
                                                     [0 for step in range(0, (timer_time * 5) + 1)]]
                        if value_mode != "ann":
                            plot_data[tag["epc"]][1][loop_counter] = tag[value_mode]
                        else:
                            plot_data[tag["epc"]][1][loop_counter] = tag["rssi"]
                        epc_out_list.append(tag["epc"])
                loop_counter += 1
            if value_mode != "ann":
                for key, value in plot_data.items():
                    plt.plot(value[0], value[1], label=key[20:])
                plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
                plt.xlabel("Time in Seconds")
                plt.ylabel(value_mode.capitalize() + " Value")
                plt.title("Tag detection for " + str(timer_time) + " Seconds with " + str(timer_power) + " dBm")
                plt.tight_layout()
                plt.show()
                enc = [0xaa, 0xbb, 0x01, 0x01, 0x02, 0x00, 0x00, 0xaa, 0xcc]  # SetMode (to NormalMode)
                message = bytes(enc)
                s.send(message)
                placeholder = s.recv(buffer)
            else:
                try:
                    ann_dataset_file = open("annDatasetTrain.json", "r")
                    ann_dataset_dict = json.loads(ann_dataset_file.read())
                except:
                    ann_dataset_dict = {}
                for key, value in plot_data.items():
                    ann_dataset_dict[str(input(key[20:] + "  r/f? ")) + str(len(ann_dataset_dict))] = value[1]
                ann_dataset_file = open("annDatasetTrain.json", "w")
                ann_dataset_file.write(json.dumps(ann_dataset_dict, sort_keys=True))
                ann_dataset_file.close()
                ann_dataset_file = open("annDatasetTrain.json", "r")
                ann_dataset_file.close()
        else:
            timer_alert_label.config(text="6 dBm <= Power <= 34 dBm!")


def createResponseOutput(response):
    handover = ["0x" + hex(int(i))[2:].zfill(2) for i in response]
    for count, value in enumerate(handover):
        if value == "0xaa" and handover[count + 1] == "0xaa":
            del handover[count]
    handover = handover[4:]
    command_id = hex(((int(handover[1], base=16) << 8) ^ (2 ** 15)) + int(handover[0], base=16))
    command_data = handover[2:]
    command_res_dict = {
        "0x101": rSyncGetEPCs,
        "0x21e": rSyncGetEPCs
    }
    r_command = command_res_dict.get(command_id)
    output = r_command(command_data)
    return output


def rSyncGetEPCs(c_data):
    tag_list = []
    info = {"type": "info", "command": "SyncGetEPCs"}
    if c_data[0] == "0x00":
        info["error"] = "none"
    elif c_data[0] == "0x0a":
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
                extended_result["phase"] = (int(c_data[1], base=16) + (int(c_data[2], base=16) << 8)) / 10 - 90
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
                                            button_SyncGetEPCs_rssi_timer.config(state=DISABLED),
                                            button_SyncGetEPCs_phase_timer.config(state=DISABLED),
                                            button_SyncGetEPCs_ann.config(state=DISABLED)],
                           state=DISABLED)
connection_status_label = Label(root, text="")
ttk.Separator(root, orient=HORIZONTAL).grid(row=2, column=0, columnspan=5, sticky='ew')
button_SyncGetEPCs_rssi_timer = Button(root,
                                       text="RSSI Determination",
                                       command=lambda: SyncGetEPCs("timer",
                                                                   "rssi",
                                                                   timer_time_entry.get(),
                                                                   timer_power_entry.get(),
                                                                   timer_rssi_threshold_entry.get()),
                                       state=DISABLED)
button_SyncGetEPCs_phase_timer = Button(root,
                                        text="Phase Determination",
                                        command=lambda: SyncGetEPCs("timer",
                                                                    "phase",
                                                                    timer_time_entry.get(),
                                                                    timer_power_entry.get(),
                                                                    timer_rssi_threshold_entry.get()),
                                        state=DISABLED)
button_SyncGetEPCs_ann = Button(root,
                                text="ANN Data",
                                command=lambda: [timer_time_entry.delete(0, END),
                                                 timer_time_entry.insert(0, 10),
                                                 SyncGetEPCs("timer",
                                                             "ann",
                                                             timer_time_entry.get(),
                                                             timer_power_entry.get(),
                                                             timer_rssi_threshold_entry.get())],
                                state=DISABLED)
timer_time_entry_label = Label(root, text="Time (s):")
timer_time_entry = Entry(root, width=8)
timer_power_entry_label = Label(root, text="Power (dBm):")
timer_power_entry = Entry(root, width=8)
timer_rssi_threshold_entry_label = Label(root, text="RSSI Threshold:", state=DISABLED)
timer_rssi_threshold_entry = Entry(root, width=8, state=DISABLED)
timer_alert_label = Label(root, text="", fg='#ff0000')
button_SyncGetEPCs_increasing_power = Button(root,
                                             text="Increasing Power Mode",
                                             command=lambda: SyncGetEPCs("power", "", 0, 0,
                                                                         timer_rssi_threshold_entry.get()),
                                             state=DISABLED)

if __name__ == '__main__':
    main()
