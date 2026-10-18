import random
import heapq
from queue import Queue

class Channel:
    def __init__(self, delay_prob: float, corruption_prob: float, loss_prob: float):
        self.delay_prob = delay_prob
        self.corruption_prob = corruption_prob
        self.loss_prob = loss_prob
        self.data_queue = []
        self.ack_queue = []
        self.delivered_data = Queue()
        self.delivered_ack = Queue()
        self.current_time = 0.0
        self.counter = 0

    def tick(self):
        self.current_time += 1

        while self.data_queue and self.data_queue[0][0] <= self.current_time:
            self.delivered_data.put(self.data_queue[0][2])
            heapq.heappop(self.data_queue)

        while self.ack_queue and self.ack_queue[0][0] <= self.current_time:
            self.delivered_ack.put(self.ack_queue[0][2])
            heapq.heappop(self.ack_queue)


    def transmit(self, packet: str, is_data: bool = True):
        parts = packet.split(":")

        if(random.random() < self.loss_prob):
            print(f"Packet {parts[1]} lost!")
            return

        if(random.random() < self.corruption_prob):
            print(f"Packet {parts[1]} corrupted!")
            parts[3] = str(int(parts[3]) + random.randint(1, 5))

            packet = ":".join(parts)

        arrival_time = self.current_time + 1.0  # Adding transmission delay

        if(random.random() < self.delay_prob):
            arrival_time += random.randint(1, 3)    # Assuming additional delay of 1 to 3 seconds
            print(f"Packet {parts[1]} delayed!")

        if(is_data):
            heapq.heappush(self.data_queue, (arrival_time, self.counter, packet))
        else:
            heapq.heappush(self.ack_queue, (arrival_time, self.counter, packet))

    def receive_packet(self):
        try:
            return self.delivered_data.get_nowait()
        except:
            return None

    def receive_ack(self):
        try:
            return self.delivered_ack.get_nowait()
        except:
            return None
