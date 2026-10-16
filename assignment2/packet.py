def get_checksum(data : str, seqnum : int):
    content = data.encode() + str(seqnum).encode()
    checksum = 0
    for i in range(0, len(content), 2):
        if(i + 1 < len(content)):
            checksum += (content[i] << 8) + content[i + 1]
        else:
            checksum += (content[i] << 8)

        checksum = (checksum & 0xFFFF) + (checksum >> 16)

    return (~checksum & 0xFFFF)

def verify_checksum(data : str, seqnum : int, checksum : int):
    return get_checksum(data, seqnum) == checksum

def make_packet(seqnum : int, data : str):
    checksum = get_checksum(data, seqnum)
    return f"{seqnum}:{data}:{checksum}"

def parse_packet(packet : str):
    parts = packet.split(":")

    if(len(parts) != 3):
        raise ValueError("Malformed packet")

    seqnum = int(parts[0])
    data = parts[1]
    checksum = int(parts[2])

    is_valid = verify_checksum(data, seqnum, checksum)

    return {seqnum, data, checksum, is_valid}