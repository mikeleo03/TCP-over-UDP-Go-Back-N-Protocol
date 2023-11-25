import time
import logging

from lib.segment import Segment
import lib.segment as segment
from lib.argparse import FileTransferArgumentParser
from lib.connection import Connection
from lib.constant import (
    SYN_FLAG,
    ACK_FLAG,
    FIN_FLAG,
    SYN_ACK_FLAG,
    FIN_ACK_FLAG,
    TIMEOUT,
)


class Client:
    def __init__(self):
        # Initialize client
        args = FileTransferArgumentParser(is_server=False)
        client_port, broadcast_port, pathfile_output = args.get_value()

        self.client_port: str = client_port
        self.broadcast_port: str = broadcast_port
        self.pathfile_output: str = pathfile_output.split("/")[-1]

        # Connection
        self.connection = Connection(
            broadcast_port=broadcast_port, port=client_port, is_server=False
        )
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
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        logger.addHandler(ch)
        return logger

    def connect(self):
        # Initialize connection to server
        self.connection.send_data(
            self.segment.get_bytes(), (self.connection.ip, self.broadcast_port)
        )

    def three_way_handshake(self):
        # Three Way Handshake Protocol, for client-side to establishing connection with server
        pass

    def listen_file_transfer(self):
        # File transfer, client-side
        request_number = 3
        data, server_address = None, None

        while True:
            try:
                data, server_address = self.connection.listen_single_segment(3)
                if server_address[1] != self.broadcast_port:
                    # Ignore segments with wrong port
                    self.logger.warning(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] "
                        f"Ignored Segment {self.segment.get_header()['seq_num']} [Wrong port]"
                    )
                    continue
                self.segment.set_from_bytes(data)

                if not self.segment.valid_checksum():
                    # Ignore segemnts with invalid checksum
                    self.logger.warning(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] "
                        f"Ignored Segment {self.segment.get_header()['seq_num']} [Invalid checksum]"
                    )
                    continue

                if self.segment.get_header()["seq_num"] == request_number:
                    # Handle data segment
                    payload = self.segment.get_payload()
                    self.file.write(payload)
                    self.logger.info(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] "
                        f"Received Segment {request_number}"
                    )
                    self.logger.info(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] "
                        f"Sending ACK {request_number + 1}"
                    )
                    request_number += 1
                    self.send_ack(server_address, request_number)
                    continue

                if self.segment.get_flag() == FIN_FLAG:
                    # Handle FIN segment
                    self.logger.info(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] Received FIN"
                    )
                    break
                if self.segment.get_header()["seq_num"] < request_number:
                    self.logger.warning(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] "
                        f"Ignored Segment {self.segment.get_header()['seq_num']} [Duplicate]"
                    )
                elif self.segment.get_header()["seq_num"] > request_number:
                    self.logger.warning(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] "
                        f"Ignored Segment {self.segment.get_header()['seq_num']} [Out-Of-Order]"
                    )
                else:
                    self.logger.warning(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] "
                        f"Ignored Segment {self.segment.get_header()['seq_num']} [Corrupt]"
                    )

                self.send_ack(server_address, request_number)

            except socket_timeout:
                self.logger.warning(
                    f"[!] [Server {server_address[0]}:{server_address[1]}] "
                    f"[Timeout] timeout error, resending prev seq num"
                )
            self.send_ack(server_address, request_number)

        self.logger.info(
            f"[!] [Server {server_address[0]}:{server_address[1]}] Data received successfully"
        )

        self.logger.info(
            f"[!] [Server {server_address[0]}:{server_address[1]}] Writing file to out/{self.pathfile_output}"
        )

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
