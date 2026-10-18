from channel import Channel
from packet import make_packet, parse_packet, generate_packets
import time
import threading

class SRSender:
    def __init__(self, channel: Channel, total_packets: int, window_size: int, max_time: float, sequence_bits: int):
        self.channel = channel
        self.seq_mod = 2 ** sequence_bits
        self.packets = generate_packets(total_packets, self.seq_mod)
        self.base = 0
        self.next_seq = 0
        self.window_size = window_size
        self.max_time = max_time
        self.acked = [False] * total_packets
        self.send_time = {}

    def send_packets(self):
        while (self.next_seq - self.base < self.window_size and self.next_seq < len(self.packets)):
            packet = self.packets[self.next_seq]
            self.channel.transmit(packet, is_data=True)
            print(f"Sender: Packet {self.next_seq % self.seq_mod} sent!")

            self.send_time[self.next_seq] = self.channel.current_time
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

        if self.acked[ack_index]:
            print(f"Sender: Packet {ack_index} already acknowledged!")
            return

        self.acked[ack_index] = True
        print(f"Sender: Packet {ack_seq} marked as acknowledged")

        temp = self.base

        while self.base < len(self.packets) and self.acked[self.base]:
            self.base += 1

        if self.base != temp:
            print(f"Sender: Window base moved to {self.base}")


    def handle_timeout(self):
        if self.base == self.next_seq:
            return

        for i in range(self.base, self.next_seq):
            if self.acked[i]:
                continue

            if self.channel.current_time - self.send_time[i] >= self.max_time:
                print(f"Sender: Packet {i % self.seq_mod} timed out")

                self.channel.transmit(self.packets[i], True)
                self.send_time[i] = self.channel.current_time

                print(f"Sender: Retransmitting packet {i % self.seq_mod}")

    def run(self):
        while self.base < len(self.packets):

            self.send_packets()

            self.receive_ack()

            self.handle_timeout()

            time.sleep(0.01)

        print("Sender: All packets acknowledged!")

class SRReceiver:
    def __init__(self, channel: Channel, event, sequence_bits: int, window_size: int):
        self.channel = channel
        self.seq_mod = 2 ** sequence_bits
        self.stop_event = event
        self.window_size = window_size
        self.base = 0
        self.buffer = {}

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
        offset = (seqnum - self.base) % self.seq_mod

        if offset < self.window_size:
            if seqnum in self.buffer:
                print(f"Receiver: Duplicate Packet {seqnum} received. Already buffered")
            else:
                print(f"Receiver: Packet {seqnum} received. Buffering")
                self.buffer[seqnum] = packet_obj["data"]

            while self.base % self.seq_mod in self.buffer:
                key = self.base % self.seq_mod
                print(f"Receiver: Packet {self.base % self.seq_mod} delivered! Message: {self.buffer[key]}")
                self.buffer.pop(key)
                self.base += 1

        else:
            print(f"Receiver: Packet {seqnum} is already delivered!")

        return True, seqnum

    def send_ack(self, seqnum):
        if seqnum is None:
            return

        ack_packet = make_packet(seqnum, "", "ACK")
        self.channel.transmit(ack_packet, is_data=False)

        print(f"Receiver: Sending ACK {seqnum}")

    def run(self):
        while not self.stop_event.is_set():
            received, seqnum = self.receive_packet()

            if not received:
                time.sleep(0.01)
                continue

            self.send_ack(seqnum)

            time.sleep(0.01)

        print("Receiver: Simulation finished.")

def run_sr(total_packets, window_size, sequence_bits, loss_prob, corruption_prob, delay_prob, timeout_duration):

    if sequence_bits < 1:
        raise ValueError("Sequence bits must be at least 1")

    seq_mod = 2 ** sequence_bits

    if window_size < 1 or window_size > seq_mod // 2:
        raise ValueError(f"Window size must be between 1 and {seq_mod // 2}")

    channel = Channel(delay_prob, corruption_prob, loss_prob)

    stop_event = threading.Event()

    sender = SRSender(channel, total_packets, window_size, timeout_duration, sequence_bits)

    receiver = SRReceiver(channel, stop_event, sequence_bits, window_size)

    sender_thread = threading.Thread(target=sender.run)
    receiver_thread = threading.Thread(target=receiver.run)

    def clock():
        while not stop_event.is_set():
            channel.tick()
            time.sleep(0.1)

    clock_thread = threading.Thread(target=clock)

    print("Starting SR simulation!")

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

    print("SR simulation finished!")


if __name__ == "__main__":
    run_sr(200, 4, 3, 0.05, 0.05, 0.1, 2)