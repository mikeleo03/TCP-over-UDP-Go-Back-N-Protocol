import socket
from typing import Tuple
from segment import Segment
from constant import DEFAULT_BROADCAST_PORT, DEFAULT_IP, DEFAULT_PORT, SEGMENT_SIZE, TIMEOUT

class Connection:
    def __init__(self, ip : str = DEFAULT_IP, broadcast_port: int = DEFAULT_BROADCAST_PORT, port: int = DEFAULT_PORT, is_server: bool = False):
        # Init UDP socket
        if is_server:
            self.ip = ip
            self.port = broadcast_port
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Source : https://docs.python.org/3/library/socket.html
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((ip, broadcast_port))
            print(f"[!] Server started at {self.ip}:{self.port}")
        else:
            self.ip = ip
            self.port = broadcast_port
            self.client_port = port
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((ip, port))
            print(f"[!] Client started at {self.ip}:{self.port}")

    def send_data(self, msg: Segment, dest: Tuple[str, int]):
        # Send single segment into destination
        self.socket.sendto(msg, dest)

    def listen_single_segment(self, timeout=TIMEOUT) -> Segment:
        # Listen single UDP datagram within timeout and convert into segment
        try:
            self.socket.settimeout(timeout)
            return self.socket.recvfrom(SEGMENT_SIZE)
        except TimeoutError as e:
            raise e

    def close_socket(self):
        # Release UDP socket
        self.socket.close()
        
    def __str__(self):
        # String overriding for easier print(connection)
        print(f"ip: {self.ip}\n broadcast_port: {self.port}\n  client port:{self.client_port}\n")
        