from gbn import run_gbn
from sr import run_sr

def main():
    protocol = input("Protocol (gbn/sr): ").strip().lower()
    total_packets = int(input("Number of packets [200]: ") or 200)
    window_size = int(input("Window size [4]: ") or 4)
    sequence_bits = int(input("Sequence bits [3]: ") or 3)
    loss_prob = float(input("Loss probability [0.05]: ") or 0.05)
    corruption_prob = float(input("Corruption probability [0.05]: ") or 0.05)
    delay_prob = float(input("Delay probability [0.1]: ") or 0.1)
    
    if protocol == "gbn":
        run_gbn(total_packets, window_size, sequence_bits, loss_prob, corruption_prob, delay_prob, 5)
    elif protocol == "sr":
        run_sr(total_packets, window_size, sequence_bits, loss_prob, corruption_prob, delay_prob, 5)
    else:
        print("Unknown protocol. Enter gbn or sr.")

if __name__ == "__main__":
    main()