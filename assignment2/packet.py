def get_checksum(data : str, seqnum : int, packet_type : str):
    content = data.encode() + str(seqnum).encode() + packet_type.encode()
    checksum = 0
    for i in range(0, len(content), 2):
        if(i + 1 < len(content)):
            checksum += (content[i] << 8) + content[i + 1]
        else:
            checksum += (content[i] << 8)

        checksum = (checksum & 0xFFFF) + (checksum >> 16)

    return (~checksum & 0xFFFF)

def verify_checksum(data : str, seqnum : int, checksum : int, packet_type: str):
    return get_checksum(data, seqnum, packet_type) == checksum

def make_packet(seqnum : int, data : str, packet_type: str):
    checksum = get_checksum(data, seqnum, packet_type)
    return f"{packet_type}:{seqnum}:{data}:{checksum}"

def parse_packet(packet : str):
    parts = packet.split(":")

    if(len(parts) != 4):
        raise ValueError("Malformed packet")

    packet_type = parts[0]
    seqnum = int(parts[1])
    data = parts[2]
    checksum = int(parts[3])

    is_valid = verify_checksum(data, seqnum, checksum, packet_type)

    return {"type": packet_type, "seqnum": seqnum, "data": data, "checksum": checksum, "is_valid": is_valid}

def generate_packets(n: int, seq_mod):
    packets = []
    for i in range(n):
        packets.append(make_packet(i % seq_mod, f"Hi From Packet {i}", "DATA"))

    return packets