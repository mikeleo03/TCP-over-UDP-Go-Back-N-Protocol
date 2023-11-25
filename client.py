import time
import logging
import colorlog
from socket import timeout 

from lib.segment import Segment
from lib.argparse import FileTransferArgumentParser
from lib.connection import Connection
from lib.constant import SYN_FLAG, ACK_FLAG, FIN_FLAG, SYN_ACK_FLAG, TIMEOUT, TIMEOUT_LISTEN

class Client:
    def __init__(self):
        # Initialize client
        args = FileTransferArgumentParser(is_server=False)
        client_arguments = args.get_value()

        self.client_port: int = client_arguments["client_port"]
        self.broadcast_port: int = client_arguments["broadcast_port"]
        self.pathfile_output: str = client_arguments["pathfile_output"].split("/")[-1]

        # Connection
        self.connection = Connection(broadcast_port=self.broadcast_port, port=self.client_port, is_server=False)
        self.segment = Segment()

        # File
        self.file = self.create_file()

        # Logger
        self.logger = self.setup_logger()

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

    def connect(self):
        # Initialize connection to server
        self.connection.send_data(self.segment.get_bytes(), (self.connection.ip, self.broadcast_port))

    def three_way_handshake(self):
        # Three Way Handshake Protocol, for client-side to establishing connection with server
        while True:
            data, server_address = None, ("127.0.0.1", self.broadcast_port)
            try:
                # Receive data from server
                data, server_address = self.connection.listen_single_segment(TIMEOUT_LISTEN)
                self.segment.set_from_bytes(data)

                # Check flag in segment
                # If segment flag is SYN, server want to establish connection. Send SYN-ACK flag.
                if self.segment.get_flag() == SYN_FLAG:
                    # Set SYN-ACK flag
                    self.segment.set_flag(["SYN", "ACK"])

                    # Initialize sequence and ACK number in segment header
                    segment_header = self.segment.get_header()
                    segment_header["ack_num"] = segment_header["seq_num"] + 1
                    segment_header["seq_num"] = 0

                    # Show status
                    self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Sending SYN-ACK")

                    # Send segment to server
                    self.connection.send_data(self.segment.get_bytes(), server_address)
                # If segment flag is SYN-ACK, resend that flag to server.
                elif self.segment.get_flag() == SYN_ACK_FLAG:
                    # Show status
                    self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Resending SYN-ACK")

                    # Resend the same segment to server
                    self.connection.send_data(self.segment.get_bytes(), server_address)
                # If segment flag is ACK, then three-way handshake is completed
                elif self.segment.get_flag() == ACK_FLAG:
                    # Show status
                    self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Received ACK")
                    self.logger.info(f"[!] [Server {server_address[0]}:{server_address[1]}] Connection established")
                    break
                # Other than that, reset connection with server. Send SYN-ACK to server
                else:
                    # Set SYN-ACK flag
                    self.segment.set_flag(["SYN", "ACK"])

                    # Reset sequence and ACK number in segment header
                    segment_header = self.segment.get_header()
                    segment_header["ack_num"] = 1
                    segment_header["seq_num"] = 0

                    # Show status
                    self.logger.warning(f"[!] [Server {server_address[0]}:{server_address[1]}] Segment file received. Resetting connection to server")
                    self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Sending SYN-ACK")

                    # Send segment to server
                    self.connection.send_data(self.segment.get_bytes(), server_address)
            except timeout:
                # If timeout happened when waiting for server ACK flag (third phase of handshake)
                if self.segment.get_flag() == SYN_ACK_FLAG:
                    self.logger.error(f"[!] [Server {server_address[0]}:{server_address[1]}] ACK response timeout")
                # Other than that, timeout happened when waiting for server SYN flag
                else:
                    self.logger.error(f"[!] [Server {server_address[0]}:{server_address[1]}] SYN response timeout")

    def listen_file_transfer(self):
        # File transfer, client-side
        request_number = 2
        data, server_address = None, None

        while True:
            try:
                data, server_address = self.connection.listen_single_segment(3)
                if server_address[1] == self.broadcast_port:
                    self.segment.set_from_bytes(data)
                    if self.segment.valid_checksum() and self.segment.get_header()["seq_num"] == request_number:
                        payload = self.segment.get_payload()
                        self.file.write(payload)
                        self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Received Segment {request_number}")
                        self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Sending ACK {request_number + 1}")
                        request_number += 1
                        self.send_ack(server_address, request_number)
                        continue
                    elif self.segment.get_flag() == FIN_FLAG:
                        # Handle FIN segment
                        self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Received FIN")
                        break
                    elif self.segment.get_header()["seq_num"] < request_number:
                        self.logger.warning(f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Duplicate]")
                    elif self.segment.get_header()["seq_num"] > request_number:
                        self.logger.warning(f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Out-Of-Order]")
                    else:
                        if not self.segment.valid_checksum():
                            self.logger.warning(f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Invalid-Checksum]")
                        else:
                            self.logger.warning(f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Corrupt]")
                else:
                    # Ignore segments with wrong port
                    self.logger.warning(f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Wrong-Port]")
                
                self.send_ack(server_address, request_number)
            
            except timeout:
                self.logger.error(f"[!] [Server {server_address[0]}:{server_address[1]}] Timeout error. Resending previous sequence number")
                self.send_ack(server_address, request_number)

        # Send FIN-ACK
        self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Sending FIN-ACK")
        finack = Segment()
        finack.set_header({"ack_num": request_number, "seq_num": request_number})
        finack.set_flag(["FIN", "ACK"])
        self.connection.send_data(finack.get_bytes(), server_address)

        ack = False
        timeout = time.time() + TIMEOUT_LISTEN
        while not ack:
            try:
                (data, server_address) = self.connection.listen_single_segment()
                ack_segment = Segment()
                ack_segment.set_from_bytes(data)

                if ack_segment.get_flag() == ACK_FLAG:
                    self.logger.debug(f"[!] [Server {server_address[0]}:{server_address[1]}] Received ACK. Tearing down connection.")
                    ack = True
                    
            except timeout:
                if time.time() > TIMEOUT:
                    self.logger.warning(f"[!] [Server {server_address[0]}:{server_address[1]}] Waiting for too long. Connection closed")
                    break
                self.logger.warning(f"[!] [Server {server_address[0]}:{server_address[1]}] Timeout error. Resending FIN-ACK")
                self.connection.send_data(finack.get_bytes(), server_address)

        self.logger.info(f"[!] [Server {server_address[0]}:{server_address[1]}] Data received successfully")
        self.logger.info(f"[!] [Server {server_address[0]}:{server_address[1]}] Writing file to out/{self.pathfile_output}")

    def create_file(self):
        # Create file to store received data
        try:
            file = open(f"out/{self.pathfile_output}", "wb")
            return file
        except FileNotFoundError:
            self.logger.error(f"[!] {self.pathfile_output} doesn't exist. Exiting...")
            exit(1)

    def send_ack(self, server_address, ack_number):
        # Send ack to server
        response = Segment()
        response.set_flag(["ACK"])
        header = response.get_header()
        header["seq_num"] = ack_number - 1
        header["ack_num"] = ack_number
        response.set_header(header)
        self.connection.send_data(response.get_bytes(), server_address)

    def shutdown(self):
        # Close file and connection
        self.file.close()
        self.connection.close_socket()

if __name__ == "__main__":
    main = Client()
    main.connect()
    main.three_way_handshake()
    main.listen_file_transfer()
    main.shutdown()