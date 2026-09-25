import socket
import struct
import random

# RCODE mapping according to RFC 1035
RCODE_MAP = {
    0: "NoError (No error condition)",
    1: "FormErr (Format error in query)",
    2: "ServFail (Server failure)",
    3: "NXDOMAIN (Non-Existent Domain)",
    4: "NotImp (Not Implemented)",
    5: "Refused (Query Refused)"
}

def encode_qname(domain: str) -> bytes:
    qname = b""
    for label in domain.strip('.').split('.'):
        encoded_label = label.encode('ascii')
        qname += bytes([len(encoded_label)]) + encoded_label
    qname += b"\x00"
    return qname

def parse_name(data: bytes, offset: int) -> tuple[str, int]:
    labels = []
    jumped = False
    initial_offset = offset
    
    while True:
        if offset >= len(data):
            raise ValueError("Name offset out of bounds.")
            
        length = data[offset]
        
        # End of name label
        if length == 0:
            if not jumped:
                offset += 1
            break
            
        # Check for compression pointer (top 2 bits set: 0xC0)
        if (length & 0xC0) == 0xC0:
            if offset + 1 >= len(data):
                raise ValueError("Pointer Error")
            pointer = struct.unpack("!H", data[offset:offset+2])[0] & 0x3FFF
            if not jumped:
                initial_offset = offset + 2
                jumped = True
            offset = pointer
        else:
            offset += 1
            labels.append(data[offset:offset+length].decode('ascii', errors='ignore'))
            offset += length
            
    final_offset = initial_offset if jumped else offset
    return ".".join(labels), final_offset

def build_dns_query(domain: str, tx_id: int) -> bytes:
    # Header: TxID, Flags (0x0100 = Standard query with Recursion Desired), QDCOUNT=1
    flags = 0x0100
    qdcount = 1
    ancount = 0
    nscount = 0
    arcount = 0
    
    header = struct.pack("!HHHHHH", tx_id, flags, qdcount, ancount, nscount, arcount)
    
    # Question: QNAME, QTYPE=1 (A record), QCLASS=1 (IN - Internet)
    qname = encode_qname(domain)
    qtype = 1
    qclass = 1
    question = qname + struct.pack("!HH", qtype, qclass)
    
    return header + question

def parse_dns_response(data: bytes, expected_tx_id: int):
    if len(data) < 12:
        print("Received packet is too short!")
        return

    # 1. Parse Header (12 bytes)
    tx_id, flags, qdcount, ancount, nscount, arcount = struct.unpack("!HHHHHH", data[:12])
    
    # Verify Transaction ID
    if tx_id != expected_tx_id:
        print(f"[-] Warning: Transaction ID mismatch! Expected {expected_tx_id}, got {tx_id}")

    # Flags extraction
    qr = (flags >> 15) & 0x1
    aa = (flags >> 10) & 0x1
    tc = (flags >> 9) & 0x1
    rd = (flags >> 8) & 0x1
    ra = (flags >> 7) & 0x1
    rcode = flags & 0x0F
    
    rcode_str = RCODE_MAP.get(rcode, f"Unknown RCODE ({rcode})")

    print("DNS Response details:")
    print(f"Transaction ID      : 0x{tx_id:04X} ({tx_id})")
    print(f"Response Status     : {rcode_str}")
    print(f"Flags               : QR={qr}, AA={aa}, TC={tc}, RD={rd}, RA={ra}")
    print(f"Counts              : Questions={qdcount}, Answers={ancount}, Authority={nscount}, Additional={arcount}")
    
    offset = 12
    
    # 2. Skip/Parse Question Section
    try:
        for _ in range(qdcount):
            qname, offset = parse_name(data, offset)
            qtype, qclass = struct.unpack("!HH", data[offset:offset+4])
            offset += 4
            qtype_str = "A" if qtype == 1 else str(qtype)
            print(f"Query Name  : {qname}")
            print(f"Query Type  : {qtype_str} (Class: {qclass})")
    except Exception as e:
        print(f"Error parsing Question Section: {e}")
        return

    if rcode != 0:
        print(f"\nQuery failed with status: {rcode_str}")
        return

    if ancount == 0:
        print("\nResponse received, but no Answer records returned.")
        return

    print("\nAnswer Records: \n")
    
    for i in range(ancount):
        try:
            name, offset = parse_name(data, offset)
            rtype, rclass, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset+10])
            offset += 10
            rdata = data[offset:offset+rdlength]
            offset += rdlength
            
            if rtype == 1 and rdlength == 4:  # Type A record (IPv4)
                ip_addr = socket.inet_ntoa(rdata)
                print(f"[{i+1}] Name: {name}")
                print(f"Type: A (IPv4) | TTL: {ttl} seconds")
                print(f"Resolved IP: {ip_addr}")
            elif rtype == 5:  # Type CNAME record
                cname, _ = parse_name(data, offset - rdlength)
                print(f"[{i+1}] Name: {name}")
                print(f"Type: CNAME | TTL: {ttl} seconds")
                print(f"Canonical Name: {cname}")
            else:
                print(f"[{i+1}] Name: {name}")
                print(f"Type: {rtype} | TTL: {ttl} seconds | Length: {rdlength}")
        except Exception as e:
            print(f"[-] Error parsing Answer Record #{i+1}: {e}")
            break

def query_dns_server(dns_server: str, domain: str, timeout: int = 5):
    domain = domain.strip()
    if not domain or len(domain) > 253:
        print("Invalid domain name!")
        return

    tx_id = random.randint(1, 65535)
    packet = build_dns_query(domain, tx_id)
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.sendto(packet, (dns_server, 53))
            response, _ = sock.recvfrom(4096)
            parse_dns_response(response, tx_id)
        except socket.timeout:
            print(f"\nRequest timed out. No response from DNS server {dns_server} within {timeout}s.")
        except socket.gaierror:
            print(f"\nInvalid DNS server IP address: '{dns_server}'")
        except Exception as e:
            print(f"\nsocket error occurred: {e}")

def main():
    dns_server = input("Enter DNS Server IP (e.g., 8.8.8.8): ").strip()
    if not dns_server:
        dns_server = "8.8.8.8"
        print(f"No IP provided. Defaulting to {dns_server}")

    while True:
        domain = input("Enter domain name('q' to quit): ").strip()
        
        if domain.lower() == 'q':
            print("Exiting...")
            break
            
        if not domain:
            continue
            
        if domain.startswith("http://"):
            domain = domain[7:]
        elif domain.startswith("https://"):
            domain = domain[8:]
        domain = domain.split('/')[0]

        query_dns_server(dns_server, domain)


main()