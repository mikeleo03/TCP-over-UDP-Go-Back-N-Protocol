import os
import logging
import colorlog
import threading
import time

from math import ceil
import socket
from typing import List, Tuple, Dict

from lib.connection import Connection
from lib.segment import Segment
from lib.argparse import FileTransferArgumentParser as Parser
from lib.constant import SYN_FLAG, ACK_FLAG, FIN_ACK_FLAG, PAYLOAD_SIZE, SYN_ACK_FLAG, TIMEOUT_LISTEN, WINDOW_SIZE

class Server:
    # -- Constructor --
    def __init__(self):
        # Logger
        self.logger = self.setup_logger()
        
        # Init server
        args = Parser(is_server=True)
        server_arguments = args.get_value()
        self.broadcast_port : int = server_arguments["broadcast_port"]
        self.pathfile : str = server_arguments["pathfile_input"]
        self.connection = Connection(broadcast_port=self.broadcast_port, is_server=True)
        
        self.file = self.open_file()
        self.filesize = self.get_filesize()
        self.segment = Segment()
        self.client_list: List[Tuple[int, int]] = []
        self.filename = self.get_filename()
        self.breakdown_file()

        self.parallel = False

        self.logger.debug(f"[!] Source file | {self.filename} | {self.filesize} bytes")

    def setup_logger(self):
        # Set up logging configuration
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # Create formatter
        formatter = colorlog.ColoredFormatter("%(asctime)s - %(log_color)s%(message)s", 
                                              log_colors={'DEBUG': 'white',
                                                          'INFO': 'green',
                                                          'WARNING': 'yellow',
                                                          'ERROR': 'red',
                                                          'CRITICAL': 'bold_red',
                                              })

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        logger.addHandler(ch)
        return logger
    

    # -- Input File Handler --
    def open_file(self):
        try:
            file = open(f"{self.pathfile}", "rb")
            return file
        except FileNotFoundError:
            self.logger.error(f"[!] {self.pathfile} doesn't exists. Exiting...")
            exit(1)
            
    def get_filesize(self):
        try:
            filesize = os.path.getsize(self.pathfile)
            return filesize
        except FileNotFoundError:
            self.logger.error(f"[!] {self.pathfile} doesn't exists. Exiting...")
            exit(1)
            
    def get_filename(self):
        if "/" in self.pathfile:
            return self.pathfile.split("/")[-1]
        
        return self.pathfile
    
    def breakdown_file(self):
        self.list_segment: List[Segment] = []
        
        # Metadata support 
        metadata_segment = Segment()
        filename = self.filename.split(".")[0]
        extension = self.filename.split(".")[-1]
        filesize = self.filesize
        metadata = filename.encode() + ",".encode() + extension.encode() + ",".encode() + str(filesize).encode()
        metadata_segment.set_payload(metadata)
        header = metadata_segment.get_header()
        header["seq_num"] = 2
        header["ack_num"] = 0
        metadata_segment.set_header(header)
        self.list_segment.append(metadata_segment)
        
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
    

    # -- Listening Handler --
    def ask_for_parallel(self):
        choice = input("[?] Enable paralelization for server (y/n) ").lower()
        while not self.choice_valid(choice):
            print("[!] Please input correct input")
            choice = input("[?] Enable paralelization for server (y/n) ").lower()

        if choice == "y":
            self.parallel = True

    def listen_for_clients(self):
        self.logger.debug("[!] Listening to broadcast address for clients.")
        while True:
            if self.parallel:
                self.parallel_listen()
            else:
                try:
                    client = self.connection.listen_single_segment(TIMEOUT_LISTEN)
                    client_address = client[1]
                    ip, port = client_address
                    self.client_list.append(client_address)
                    self.logger.debug(f"[!] Received request from {ip}:{port}")
                    choice = input("[?] Listen more (y/n) ").lower()
                    while not self.choice_valid(choice):
                        print("[!] Please input correct input")
                        choice = input("[?] Listen more (y/n) ").lower()
                    if choice == "n":
                        print("\nClient list:")
                        for index, (ip, port) in enumerate(self.client_list):
                            print(f"{index+1}. {ip}:{port}")
                        print("")
                        break
                except socket.timeout:
                    if (len(self.client_list) == 0):
                        self.logger.error("[!] Timeout error for listening client. Exiting")
                    else:
                        self.logger.warning("[!] Timeout error for listening client")
                    break

    def parallel_listen(self):
        self.parallel_client_list: Dict[Tuple[str, int], List[Segment]] = {}
        while True:
            try:
                client = self.connection.listen_single_segment(15)
                client_address = client[1]
                if client_address not in self.parallel_client_list:
                    ip, port = client_address 
                    self.logger.debug(f"[!] Received request from {ip}:{port}")

                    self.parallel_client_list[client_address] = []
                    new_thread = threading.Thread(target=self.start_file_transfer, kwargs={"parallel_client": client_address})
                    new_thread.start()
                else:
                    self.parallel_client_list[client_address].append(client[0])
            except socket.timeout:
                self.logger.error("[!] Timeout error for listening client. Exiting")
                exit(0)

    def choice_valid(self, choice: str):
        if choice.lower() == "y":
            return "y"
        elif choice.lower() == "n":
            return "n"
        else:
            return False
        

    # -- File Transfer Handler --
    def start_file_transfer(self, parallel_client=None):
        self.logger.debug("[!] Commencing file transfer...")
        
        if self.parallel:
            self.three_way_handshake(parallel_client)
            self.file_transfer(parallel_client)
        else:
            for client in self.client_list:
                self.three_way_handshake(client)
                self.file_transfer(client)

    def get_segment(self, client_address: Tuple[str, int]):
        if self.parallel:
            just_now = time.time() + 1
            while (time.time() < just_now):
                if len(self.parallel_client_list[client_address]) > 0:
                    return self.parallel_client_list[client_address].pop(0), client_address
            raise socket.timeout
        else:
            return self.connection.listen_single_segment()
        
    def three_way_handshake(self, client_address: Tuple[str, int]) -> bool:
        # Three Way Handshake Protocol, for server-side to establishing connection with client
        self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Initiating three way handshake")

        # Set SYN flag to start establishing connection
        self.segment.set_flag(["SYN"])

        while True:
            # If segment flag is SYN flag, then send segment to client
            if self.segment.get_flag() == SYN_FLAG:
                # Initialize segment sequence and ACK number
                segment_header = self.segment.get_header()
                segment_header["ack_num"] = 0
                segment_header["seq_num"] = 0

                # Show status
                self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Sending SYN")

                # Send segment to client
                self.connection.send_data(self.segment.get_bytes(), client_address)
                
                # Wait for SYN-ACK from client
                try:
                    data, client_address = self.get_segment(client_address)
                    self.segment.set_from_bytes(data)
                except socket.timeout:
                    self.logger.error(f"[!] [Client {client_address[0]}:{client_address[1]}] SYN-ACK response timeout. Resending SYN")
            # If segment flag is SYN-ACK flag, then send ACK to client
            elif self.segment.get_flag() == SYN_ACK_FLAG:
                # Set segment ACK flag
                self.segment.set_flag(["ACK"])

                # Initialize segment sequence and ACK number
                segment_header = self.segment.get_header()
                segment_header["ack_num"] = 1
                segment_header["seq_num"] = 1
                self.segment.set_header(segment_header)
                
                # Show status
                self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Receive SYN-ACK")
                self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Sending ACK")

                # Send segment to client
                self.connection.send_data(self.segment.get_bytes(), client_address)
                break
            # Other than that, stop three way handshake
            else:
                self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Client already waiting for file. Ending three way handshake")
        
        self.logger.info(f"[!] [Client {client_address[0]}:{client_address[1]}] Handshake established")
    
    def file_transfer(self, client_address: Tuple[str, int]):
        # File transfer, server-side
        # seq_num 0 for SYN
        # seq_num 1 for ACK
        # seq_num 2 for Metadata
        num_of_segment = len(self.list_segment) + 2
        window_size = min(num_of_segment - 2, WINDOW_SIZE)
        sequence_base = 2
        reset_conn = False
        while sequence_base < num_of_segment and not reset_conn:
            sequence_max = window_size
            
            for i in range(sequence_max):
                # Start sending segment x
                self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Sending Segment {sequence_base + i}")
                if i + sequence_base < num_of_segment:
                    self.connection.send_data(self.list_segment[i + sequence_base - 2].get_bytes(), client_address)
                    
            for i in range(sequence_max):
                try:
                    data, response_address = self.get_segment(client_address)
                    segment = Segment()
                    segment.set_from_bytes(data)

                    # Various segment conditions
                    if (client_address[1] == response_address[1] and segment.get_flag() == ACK_FLAG and segment.get_header()["ack_num"] == sequence_base + 1):
                        self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Received ACK {sequence_base + 1}")
                        sequence_base += 1
                        window_size = min(num_of_segment - sequence_base, WINDOW_SIZE)
                    elif client_address[1] != response_address[1]:
                        self.logger.warning(f"[!] [Client {client_address[0]}:{client_address[1]}] Received ACK from wrong client")
                    elif segment.get_flag() == SYN_ACK_FLAG:
                        self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Received SYN ACK Flag, client ask to reset connection")
                        reset_conn = True
                        break
                    elif segment.get_flag() != ACK_FLAG:
                        self.logger.warning(f"[!] [Client {client_address[0]}:{client_address[1]}] Received Wrong Flag")
                    else:
                        self.logger.warning(f"[!] [Client {client_address[0]}:{client_address[1]}] Received Wrong ACK")
                        request_number = segment.get_header()["ack_num"]
                        if (request_number > sequence_base):
                            sequence_max = (sequence_max - sequence_base) + request_number
                            sequence_base = request_number

                except socket.timeout:
                    self.logger.error(f"[!] [Client {client_address[0]}:{client_address[1]}] ACK response timeout. Resending previous sequence number")
        
        if reset_conn:
            self.three_way_handshake(client_address)
            self.file_transfer(client_address)
        else:
            self.logger.info(f"[!] [Client {client_address[0]}:{client_address[1]}] File transfer complete. Sending FIN")
            sendFIN = Segment()
            sendFIN.set_flag(["FIN"])
            self.connection.send_data(sendFIN.get_bytes(), client_address)
            is_ack = False

            # Wait for ack
            while not is_ack:
                try:
                    data, response_address = self.get_segment(client_address)
                    segment = Segment()
                    segment.set_from_bytes(data)
                    if (client_address[1] == response_address[1] and segment.get_flag() == FIN_ACK_FLAG):
                        self.logger.debug(f"[!] [Client {client_address[0]}:{client_address[1]}] Received FIN-ACK")
                        sequence_base += 1
                        is_ack = True
                        if self.parallel:
                            self.parallel_client_list.pop(client_address)
                        
                except socket.timeout:
                    self.logger.error(f"[!] [Client {client_address[0]}:{client_address[1]}] ACK response timeout. Resending FIN")
                    self.connection.send_data(sendFIN.get_bytes(), client_address)

            # send ACK and tear down connection
            self.logger.info(f"[!] [Client {client_address[0]}:{client_address[1]}] Sending ACK. Tearing down connection.")
            segmentACK = Segment()
            segmentACK.set_flag(["ACK"])
            self.connection.send_data(segmentACK.get_bytes(), client_address)

if __name__ == '__main__':
    main = Server()
    main.ask_for_parallel()
    main.listen_for_clients()
    if not main.parallel:
        main.start_file_transfer()