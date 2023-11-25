from constant import CRC_POLYNOM, CRC_START

class CRC16:
    def __init__(self, data : bytes):
        # At construction of class, save data which checksum needs to be calculated. Save length of data too.
        self.data = data
        self.length = len(data)

    def calculate(self):
        # Initialize CRC register value
        crc_val = CRC_START

        # Loop to perform division for every byte of data
        for byte in self.data:
            target_byte = byte

            # Loop for every bit in target byte
            for i in range(8):
                # Get MSB of CRC value (And-operation with 0x8000 to masks MSB, shift 8 bit to right)
                crc_msb = (crc_val & 0x8000) >> 8

                # Get MSB of target byte (And-operation with 0x80 to masks MSB)
                byte_msb = (target_byte & 0x80)

                # Check whether MSB of CRC value and target byte different or not
                msb_is_same = (crc_msb ^ byte_msb)

                # Shift crc value by 1 and masks
                crc_val = (crc_val << 1) & 0xFFFF

                # If MBS is same, perform XOR with the polynom
                if msb_is_same:
                    crc_val = crc_val ^ CRC_POLYNOM

                # Shift target byte by 1 and masks
                target_byte = (target_byte << 1) & 0xFF
        
        # Return checksum with masks
        return crc_val & 0xFFFF