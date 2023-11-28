# Functions to do hamming ecc
# Implemented using most popular, 7-bit hamming encoding
def encode_hamming(plain_data):
    # Initial processing the plain data
    data = list(plain_data)
    data.reverse()      # reversing
    num_parity, num_parity_processed, data_pos, redundant, encoded = 0, 0, 0, 0, []

    # Calculate numbers of redundant bit
    while ((len(plain_data) + redundant + 1) > (pow(2, redundant))):
        redundant += 1

    # Filling the encoded with data and 0 if it is parity
    for i in range (0, (redundant + len(data))):
        parity_pos = (2 ** num_parity)
        
        if (parity_pos == (i + 1)):
            encoded.append(0)   # Init with 0
            num_parity += 1
        else:
            encoded.append(int(data[data_pos])) # Just insert the data
            data_pos += 1

    # Calculating the parity value
    for parity in range (0, (len(encoded))):
        parity_pos_onprocess = (2 ** num_parity_processed)
        
        # Searching the parity positions
        if (parity_pos_onprocess == (parity + 1)):
            startIndex = parity_pos_onprocess - 1
            i = startIndex
            toXor = []  # Array to init every value to be xor-ed

            while (i < len(encoded)):
                block = encoded[i:i + parity_pos_onprocess]
                toXor.extend(block)
                i += 2 * parity_pos_onprocess
            
            # Doing xor
            for z in range (1, len(toXor)):
                encoded[startIndex] = encoded[startIndex] ^ toXor[z]
            
            num_parity_processed += 1

    # Return the encoded
    encoded.reverse()
    return ''.join(map(str, encoded))

def detect_error(encoded_data) :
    # Initial process the encoded data
    data = list(encoded_data)
    data.reverse()
    num_parity, num_parity_processed, error, encoded, parity_list, h_copy = 0, 0, 0, [], [], []

    # Calculating numbers of parity bit
    for k in range (0, len(data)):
        parity_pos = (2 ** num_parity)
        encoded.append(int(data[k]))
        h_copy.append(data[k])
        if (parity_pos == (k + 1)):
            num_parity += 1
    
    # Try to xor-ing the parity with data using rules applied using 7-bit hamming     
    for parity in range (0, (len(encoded))):
        parity_pos_onprocess = (2 ** num_parity_processed)
        if (parity_pos_onprocess == (parity + 1)):
            startIndex = parity_pos_onprocess - 1
            i = startIndex
            toXor = []

            while (i < len(encoded)):
                block = encoded[i:i + parity_pos_onprocess]
                toXor.extend(block)
                i += 2 * parity_pos_onprocess

            for z in range (1, len(toXor)):
                encoded[startIndex] = encoded[startIndex] ^ toXor[z]
            parity_list.append(encoded[parity])
            num_parity_processed += 1
    
    parity_list.reverse()
    error = sum(int(parity_list) * (2 ** i) for i, parity_list in enumerate(parity_list[::-1]))
    
    # Return error position and he hamming copy
    return error, h_copy

def fix_error(error, hamming):
    # Turn the bits
    if (hamming[error - 1] == '0'):
        hamming[error - 1] = '1'
    elif (hamming[error - 1] == '1'):
        hamming[error - 1] = '0'

    hamming.reverse()
    
    # Return the fixed encoded hamming
    return ''.join(map(str, hamming))

def decode_hamming(encoded_data):
    # Initial processing the encoded data
    data = list(encoded_data)
    data.reverse()
    num_parity, decoded = 0, []

    # Calculating numbers of parity bit
    for k in range (0, len(data)):
        parity_pos = (2 ** num_parity)
        decoded.append(data[k])
        if (parity_pos == (k + 1)):
            num_parity += 1
            
    # Retrieve the original data from the Hamming code
    original_data = [decoded[i] for i in range(len(decoded)) if (i + 1) not in [2**j for j in range(num_parity)]]
    original_data.reverse()
    return ''.join(map(str, original_data))


# Utils
# Convert bytes to binary string
def binary_to_bytes(binary_str):
    # Ensure the binary string length is a multiple of 8 by adding padding
    padding = (8 - len(binary_str) % 8) % 8
    binary_str = '0' * padding + binary_str

    # Convert binary string to bytes
    byte_array = bytearray()
    for i in range(0, len(binary_str), 8):
        byte = int(binary_str[i:i+8], 2)
        byte_array.append(byte)

    return bytes(byte_array)


def bytes_to_binary(byte_data):
    # Converts bytes to a binary string.
    binary_str = ''.join(format(byte, '08b') for byte in byte_data)
    return binary_str


# Test
# 1. Initial
message = b"\x03\x00\x00\x00\x03\x00\x00\x00\x00\x00\x105Warna cerah yang terlihat\r\nDiriku mahir sembunyi rasa\r\nSebenarnya hitam pekat\r\nKututup rapat, jadi rahasia\r\nSatu dua kali, 'ku tak apa-apa\r\nKamu pikir hidupku baik-baik saja?\r\nSiapa yang peduli kupunya air mata?\r\nKamu hanya pinta diri berikan tawa\r\nHa-ha, ha-ha\r\nHa-ha, ha-ha, ha-ha\r\nWajah riangku perisai jitu\r\nHa-ha, ha-ha\r\nHa-ha, ha-ha, ha-ha\r\nTapi sampai kapan kubegitu?\r\nMalam hari berwahana\r\nPikiran liarku juaranya\r\nBukan 'ku tak berusaha\r\nIngin kulepas sekuat tenaga\r\nSatu dua kali, 'ku tak apa-apa\r\nKamu pikir hidupku baik-baik saja?\r\nSiapa yang peduli kupunya air mata?\r\nKamu hanya pinta diri berikan tawa, ho-oh\r\nHa-ha, ha-ha\r\nHa-ha, ha-ha, ha-ha\r\nWajah riangku perisai jitu\r\nHa-ha, ha-ha\r\nHa-ha, ha-ha, ha-ha\r\nTapi sampai kapan kubegitu?\r\nAku bulan yang terangi\r\nMalam-malammu yang sepi\r\nLalu siapa yang temani\r\nRasa gelisah kupikul sendiri\r\nHa-ho\r\n(Ha-ha, ha-ha)\r\nHa-hm, yeah\r\n(Ha-ha, ha-ha)\r\nHa-oh\r\n(Ha-ha, ha-ha)\r\nHu-hu-hu\r\nHa-ha, ha-ha\r\nHa-ha, ha-ha, ha-ha\r\nWajah riangku perisai jitu\r\nHa-ha, ha-ha\r\nHa-ha, ha-ha, ha-ha\r\nTapi sampai kapan kubegitu?\r\nHa-ha, ha-ha\r\nHa-ha, ha-ha, ha-ha\r\nWajah riangku perisai jitu (wajah riangku)\r\nHa-ha, ha-ha\r\nHa-ha, ha-ha, ha-ha (hu-uu)\r\nTapi sampai kapan kubegitu?"
print("Initial message:", message)

# 2. Convert into binary
binary_msg = bytes_to_binary(message)
print("Binary message:", binary_msg)

# 3. Applying 7-bit hamming encoding
encoded = encode_hamming(binary_msg)
print("Hamming encoded:", encoded)

# 4. Decoding hamming encoded
decoded = decode_hamming(encoded)
print("Decoded message:", decoded)

# 5. Convert back to original message
original_msg = binary_to_bytes(decoded)
print("Original message:", original_msg)

# 6. Final check, is the result original?
print("Result:", original_msg == message)
