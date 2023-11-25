import os

from math import ceil
from socket import timeout as socket_timeout
from typing import List, Tuple

from lib.connection import Connection
from lib.segment import Segment
from lib.argparse import FileTransferArgumentParser as Parser
from lib.constant import ACK_FLAG, FIN_ACK_FLAG, PAYLOAD_SIZE, SYN_ACK_FLAG, TIMEOUT_LISTEN, WINDOW_SIZE

class Server:
    def __init__(self):
        # Init server
        args = Parser(is_server=True)
        broadcast_port, pathfile_input = args.get_value()
        self.broadcast_port: str = broadcast_port
        self.pathfile: str = pathfile_input
        self.conn = Connection(broadcast_port=broadcast_port, is_server=True)
        self.file = self.open_file()
        self.filesize = self.get_filesize()
        self.segment = Segment()
        self.client_list: List[Tuple[int, int]] = []
        self.filename = self.get_filename()
        self.breakdown_file()
        print(f"[!] Source file | {self.filename} | {self.filesize} bytes")
        
    def open_file(self):
        try:
            file = open(f"{self.pathfile}", "rb")
            return file
        except FileNotFoundError:
            print(f"[!] {self.pathfile} doesn't exists. Exiting...")
            exit(1)
            
    def get_filesize(self):
        try:
            filesize = os.path.getsize(self.pathfile)
            return filesize
        except FileNotFoundError:
            print(f"[!] {self.pathfile} doesn't exists. Exiting...")
            exit(1)
            
    def get_filename(self):
        if "/" in self.pathfile:
            return self.pathfile.split("/")[-1]
        
        return self.pathfile
    
    def breakdown_file(self):
        self.list_segment: List[Segment] = []
        num_of_segment = ceil(self.filesize / PAYLOAD_SIZE)
        
        # Sending data
        for i in range(num_of_segment):
            segment = Segment()
            data_to_set = self.get_filechunk(i)
            segment.set_payload(data_to_set)
            header = segment.get_header()
            header["seq_num"] = i + 3
            header["ack_num"] = 3
            segment.set_header(header)
            self.list_segment.append(segment)
            
    def get_filechunk(self, index):
        offset = index * PAYLOAD_SIZE
        self.file.seek(offset)
        return self.file.read(PAYLOAD_SIZE)
    
    def listen_for_clients(self):
        print("[!] Listening to broadcast address for clients.")
        while True:
            try:
                client = self.conn.listen_single_segment(TIMEOUT_LISTEN)
                client_address = client[1]
                ip, port = client_address
                self.client_list.append(client_address)
                print(f"[!] Received request from {ip}:{port}")
                choice = input("[?] Listen more (y/n) ").lower()
                while not self.choice_valid(choice):
                    print("[!] Please input correct input")
                    choice = input("[?] Listen more (y/n) ").lower()
                if choice == "n":
                    print("\nClient list:")
                    for index, (ip, port) in enumerate(self.client_list):
                        print(f"{index+1} {ip}:{port}")
                    print("")
                    break
            except socket_timeout:
                print("[!] Timeout Error for listening client. exiting")
                break
            
    def choice_valid(self, choice: str):
        if choice.lower() == "y":
            return "y"
        elif choice.lower() == "n":
            return "n"
        else:
            return False
        
    def start_file_transfer(self):
        for client in self.client_list:
            self.three_way_handshake(client)
            self.file_transfer(client)

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        pass

    def file_transfer(self, client_addr: Tuple[str, int]):
        # File transfer, server-side
        # seq_num 0 for SYN
        # seq_num 1 for ACK
        num_of_segment = len(self.list_segment) + 2
        window_size = min(num_of_segment - 2, WINDOW_SIZE)
        sequence_base = 2
        reset_conn = False
        while sequence_base < num_of_segment and not reset_conn:
            sequence_max = window_size
            
            for i in range(sequence_max):
                # Start sending segment x
                print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending Segment {sequence_base + i}")
                if i + sequence_base < num_of_segment:
                    self.conn.send_data(self.list_segment[i + sequence_base - 2].get_bytes(), client_addr)
                    
            for i in range(sequence_max):
                try:
                    data, response_addr = self.conn.listen_single_segment()
                    segment = Segment()
                    segment.set_from_bytes(data)
                    
                    # Various segment conditions
                    if (client_addr[1] == response_addr[1] and segment.get_flag() == ACK_FLAG and segment.get_header()["ack"] == sequence_base + 1):
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Received ACK {sequence_base + 1}")
                        sequence_base += 1
                        window_size = min(num_of_segment - sequence_base, WINDOW_SIZE)
                    elif client_addr[1] != response_addr[1]:
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Received ACK from wrong client")
                    elif segment.get_flag() == SYN_ACK_FLAG:
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved SYN ACK Flag, client ask to reset connection")
                        reset_conn = True
                        break
                    elif segment.get_flag() != ACK_FLAG:
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved Wrong Flag")
                    else:
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Received Wrong ACK")
                        request_number = segment.get_header()["ack"]
                        if (request_number > sequence_base):
                          sequence_max = (sequence_max - sequence_base) + request_number
                          sequence_base = request_number
                except:
                    print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending prev seq num")
        
        if reset_conn:
            self.three_way_handshake(client_addr)
            self.file_transfer(client_addr)
        else:
            print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] File transfer complete, sending FIN...")
            sendFIN = Segment()
            sendFIN.set_flag(["FIN"])
            self.conn.send_data(sendFIN.get_bytes(), client_addr)
            is_ack = False

            # Wait for ack
            while not is_ack:
                try:
                    data, response_addr = self.conn.listen_single_segment()
                    segment = Segment()
                    segment.set_from_bytes(data)
                    if (client_addr[1] == response_addr[1] and segment.get_flag() == FIN_ACK_FLAG):
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved FIN-ACK")
                        sequence_base += 1
                        is_ack = True
                        
                except socket_timeout:
                    print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending FIN")
                    self.conn.send_data(sendFIN.get_bytes(), client_addr)

            # send ACK and tear down connection
            print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending ACK Tearing down connection.")
            segmentACK = Segment()
            segmentACK.set_flag(["ACK"])
            self.conn.send_data(segmentACK.get_bytes(), client_addr)


if __name__ == '__main__':
    main = Server()
    main.listen_for_clients()
    main.start_file_transfer()