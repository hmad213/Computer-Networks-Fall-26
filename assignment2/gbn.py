from channel import Channel
from packet import make_packet, parse_packet, generate_packets
import time
import threading

class GBNSender:
    def __init__(self, channel: Channel, total_packets: int, window_size: int, max_time: float, sequence_bits: int):
        self.channel = channel
        self.seq_mod = 2 ** sequence_bits
        self.packets = generate_packets(total_packets, self.seq_mod)
        self.base = 0
        self.next_seq = 0
        self.window_size = window_size
        self.max_time = max_time
        self.last_timer = 0.0

    def send_packets(self):
        while (self.next_seq - self.base < self.window_size and self.next_seq < len(self.packets)):
            if self.base == self.next_seq:
                self.last_timer = self.channel.current_time

            packet = self.packets[self.next_seq]
            self.channel.transmit(packet, is_data=True)
            print(f"Sender: Packet {self.next_seq % self.seq_mod} sent!")

            self.next_seq += 1

    def receive_ack(self):
        ack = self.channel.receive_ack()

        if not ack:
            return

        packet_obj = parse_packet(ack)

        if not packet_obj["is_valid"]:
            print("Sender: Acknowledgement received was corrupted!")
            return

        if packet_obj["type"] != "ACK":
            print("Sender: Packet type is not ACK!")
            return

        ack_seq = packet_obj["seqnum"]
        print(f"Sender: Acknowledgement {ack_seq} received!")

        ack_index = None

        for i in range(self.base, self.next_seq):
            if i % self.seq_mod == ack_seq:
                ack_index = i
                break

        if ack_index is None:
            print("Sender: Duplicate or unexpected ACK ignored!")
            return

        self.base = ack_index + 1

        print(f"Sender: Window base moved to {self.base}")

        # Restart the timer if unacknowledged packets remain
        if self.base < self.next_seq:
            self.last_timer = self.channel.current_time
        else:
            self.last_timer = None

    def handle_timeout(self):
        if self.base == self.next_seq:
            return

        if self.last_timer is not None and self.channel.current_time - self.last_timer >= self.max_time:
            print(f"Sender: Packet {self.base % self.seq_mod} timed out")

            for i in range(self.base, self.next_seq):
                self.channel.transmit(self.packets[i], True)
                print(f"Sender: Retransmitting packet {i % self.seq_mod}")

            self.last_timer = self.channel.current_time

    def run(self):
        while self.base < len(self.packets):

            self.send_packets()

            self.receive_ack()

            self.handle_timeout()

            time.sleep(0.01)

        print("Sender: All packets acknowledged!")

class GBNReceiver:
    def __init__(self, channel: Channel, event, sequence_bits: int):
        self.channel = channel
        self.seq_mod = 2 ** sequence_bits
        self.expected_seq = 0
        self.last_ack = None
        self.stop_event = event

    def receive_packet(self):
        packet = self.channel.receive_packet()

        if not packet:
            return False, None

        packet_obj = parse_packet(packet)

        if not packet_obj["is_valid"]:
            print("Receiver: Corrupted packet received!")
            return True, None

        if packet_obj["type"] != "DATA":
            print("Receiver: Packet type is not DATA!")
            return True, None

        seqnum = packet_obj["seqnum"]

        if seqnum == self.expected_seq:
            print(f"Receiver: Packet {seqnum} received successfully! Message: {packet_obj["data"]}")

            self.expected_seq = (self.expected_seq + 1) % self.seq_mod

            return True, seqnum

        print(f"Receiver: Expected packet {self.expected_seq}, but received packet {seqnum}. Discarding.")

        return True, None

    def send_ack(self, seqnum=None):
        if seqnum is not None:
            self.last_ack = seqnum

        if self.last_ack is None:
            return

        ack_packet = make_packet(self.last_ack, "", "ACK")
        self.channel.transmit(ack_packet, is_data=False)

        print(f"Receiver: Sending ACK {self.last_ack}")


    def run(self):
        while not self.stop_event.is_set():
            received, seqnum = self.receive_packet()

            if not received:
                time.sleep(0.01)
                continue

            if seqnum is not None:
                self.send_ack(seqnum)
            else:
                self.send_ack()

            time.sleep(0.01)

        print("Receiver: Simulation finished.")


def run_gbn(total_packets, window_size, sequence_bits, loss_prob, corruption_prob, delay_prob, timeout_duration):

    seq_mod = 2 ** sequence_bits

    if sequence_bits < 1:
        raise ValueError("Sequence bits must be at least 1")

    if window_size < 1 or window_size > seq_mod - 1:
        raise ValueError(f"Window size must be between 1 and {seq_mod - 1}")

    channel = Channel(delay_prob, corruption_prob, loss_prob)

    stop_event = threading.Event()

    sender = GBNSender(channel, total_packets, window_size, timeout_duration, sequence_bits)

    receiver = GBNReceiver(channel, stop_event, sequence_bits)

    sender_thread = threading.Thread(target=sender.run)
    receiver_thread = threading.Thread(target=receiver.run)

    def clock():
        while not stop_event.is_set():
            channel.tick()
            time.sleep(0.1)

    clock_thread = threading.Thread(target=clock)

    print("Starting GBN simulation!")

    receiver_thread.start()
    clock_thread.start()
    sender_thread.start()

    try:
        sender_thread.join()

        while channel.data_queue or channel.ack_queue:
            time.sleep(0.1)

    finally:
        stop_event.set()

        sender_thread.join()
        receiver_thread.join()
        clock_thread.join()

    print("GBN simulation finished!")

if __name__ == "__main__":
    run_gbn(200, 4, 3, 0.05, 0.05, 0.1, 2)