# Flag constant
SYN_FLAG = 0b000000010  # 1st bit
ACK_FLAG = 0b000010000  # 4th bit
FIN_FLAG = 0b000000001  # 0th bit
SYN_ACK_FLAG = SYN_FLAG | ACK_FLAG
FIN_ACK_FLAG = FIN_FLAG | ACK_FLAG

# Server constant
DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_BROADCAST_PORT = 9999
WINDOW_SIZE = 3

# Segment constant
SEGMENT_SIZE = 32768
PAYLOAD_SIZE = SEGMENT_SIZE - 12
TIMEOUT = 5
TIMEOUT_LISTEN = 30

# CRC constant
CRC_POLYNOM = 0x1021
CRC_START = 0xFFFF