import random

class Channel:
    def __init__(self, delay_prob: float, corruption_prob: float, loss_prob: float):
        self.delay_prob = delay_prob
        self.corruption_prob = corruption_prob
        self.loss_prob = loss_prob
        self.data_queue = []
        self.ack_queue = []

    def transmit(self, packet: str):
        parts = packet.split(":")

        if(random.random() < self.loss_prob):
            print(f"Packet {parts[0]} lost!")
            return

        if(random.random() < self.corruption_prob):
            print(f"Packet {parts[0]} corrupted!")
            parts[1] = chr(ord(parts[1][0]) + random.randint(1, 5)) + parts[1][1:]

            packet = ":".join(parts)

        self.data_queue.append(packet)

channel = Channel(0, 0.5, 0.3)
channel.transmit("1:Hello:26")
channel.transmit("2:Hello:28")
channel.transmit("3:Hello:30")
channel.transmit("4:Hello:21")
channel.transmit("5:Hello:20")
print(channel.data_queue)