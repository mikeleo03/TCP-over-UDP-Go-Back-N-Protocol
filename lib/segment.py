import struct

# Import constants
from constant import ACK_FLAG, SYN_FLAG, FIN_FLAG

class SegmentFlag:
    def __init__(self, flag : bytes):
        # Init flag variable from flag byte
        self.syn = flag & SYN_FLAG
        self.ack = flag & ACK_FLAG
        self.fin = flag & FIN_FLAG
        
    def get_flag(self) -> int:
        # Flag getter
        return self.syn | self.ack | self.fin

    def get_flag_bytes(self) -> bytes:
        # Convert this object to flag in byte form
        return struct.pack("B", self.get_flag())

class Segment:
    # -- Internal Function --
    def __init__(self):
        # Initalize segment
        self.seqNum = 0
        self.ackNum = 0
        self.flag = SegmentFlag(0b0)   # Default to 0
        self.checksum = 0
        self.data = b""  # Binary data

    def __str__(self):
        # Optional, override this method for easier print(segmentA)
        output = ""
        output += f"{'SeqNum':12}\t\t| {self.seqNum}\n"
        output += f"{'AckNum':12}\t\t| {self.ackNum}\n"
        output += f"{'FlagSYN':12}\t\t| {self.flag.syn >> 1}\n"
        output += f"{'FlagACK':12}\t\t| {self.flag.ack >> 4}\n"
        output += f"{'FlagFIN':12}\t\t| {self.flag.fin}\n"
        output += f"{'Checksum':24}| {self.checksum}\n"
        output += f"{'MsgSize':24}| {len(self.data)}\n"
        return output

    def __calculate_checksum(self) -> int:
        # Calculate checksum here, return checksum result
        # TODO : implement checksum
        pass


    # -- Setter --
    def set_header(self, header : dict):
        self.seqNum = header["seq"]
        self.ackNum = header["ack"]

    def set_payload(self, payload : bytes):
        self.data = payload

    def set_flag(self, flag_list : list):
        new_flag = 0b0
        for flag in flag_list:
            if flag == "SYN":
                new_flag |= SYN_FLAG
            elif flag == "ACK":
                new_flag |= ACK_FLAG
            elif flag == "FIN":
                new_flag |= FIN_FLAG
        self.flag = SegmentFlag(new_flag)


    # -- Getter --
    def get_flag(self) -> SegmentFlag:
        return self.flag.get_flag()

    def get_header(self) -> dict:
        return {"seq": self.seq, "ack": self.ack}

    def get_payload(self) -> bytes:
        return self.data


    # -- Marshalling --
    def set_from_bytes(self, src : bytes):
        # From pure bytes, unpack() and set into python variable
        self.seqNum = struct.unpack("I", src[0:4])[0]               # Byte 0-3 (unsigned int [4])
        self.ackNum = struct.unpack("I", src[4:8])[0]               # Byte 4-7 (unsigned int [4])
        self.flag = SegmentFlag(struct.unpack("B", src[8:9])[0])    # Byte 8 (unsigned char [1])
        # Byte 9 empty -> padding
        self.checksum = struct.unpack("H", src[10:12])[0]           # Byte 10-11 (unsigned short [2])
        self.data = src[12:]                                        # Byte 12-end -> payload

    def get_bytes(self) -> bytes:
        # Convert this object to pure bytes
        self.checksum = self.__calculate_checksum()
        res = b""
        res += struct.pack("I", self.seqNum)        # Byte 0-3 (unsigned int [4])
        res += struct.pack("I", self.ackNum)        # Byte 4-7 (unsigned int [4])
        res += self.flag.get_flag_bytes()           # Byte 8 (unsigned char [1])
        res += struct.pack("x")                     # Byte 9 -> padding
        res += struct.pack("H", self.checksum)      # Byte 10-11 (unsigned short [2])
        res += self.data                            # Byte 12-end -> payload
        return res


    # -- Checksum --
    def valid_checksum(self) -> bool:
        # Use __calculate_checksum() and check integrity of this object
        return self.__calculate_checksum() == self.checksum