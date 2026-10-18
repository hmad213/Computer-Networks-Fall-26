# CN Assignment 2: Simulating GBN and SR

Go-Back-N (GBN) and Selective Repeat (SR) reliable data transfer protocols, running over a simulated channel that can lose, corrupt and delay both data packets and ACKs. Corruption is detected with a checksum, and every send, receive, ACK, loss, timeout and retransmission is printed to the log.

## Files

| File | Purpose |
|---|---|
| `main.py` | Entry point. Asks for the protocol and inputs, then runs the simulation. |
| `gbn.py` | Go-Back-N sender, receiver and `run_gbn`. |
| `sr.py` | Selective Repeat sender, receiver and `run_sr`. |
| `channel.py` | The channel class (loss, corruption, delay, FIFO delivery, tick clock). |
| `packet.py` | Packet creation, checksum and parsing. |
| `tests.py` | Runs both protocols under the three required scenarios and prints the results table. |

## Requirements

- Python 3.8 or later

## How to run

Run:

```
python main.py
```

The program prompts for each setting. Press Enter at a prompt to accept the default shown in brackets. The protocol has no default and must be typed as `gbn` or `sr`.

## Parameters

| Prompt | Meaning | Default |
|---|---|---|
| Protocol | `gbn` or `sr` | none |
| Number of packets | How many data packets the sender transmits | 200 |
| Window size | Sender window N. GBN: at most `2^k - 1`. SR: at most `2^(k-1)`. | 4 |
| Sequence bits | k. Sequence numbers wrap modulo `2^k`. | 3 |
| Loss probability | Chance a packet or ACK is lost (0 to 1) | 0.05 |
| Corruption probability | Chance a packet or ACK is corrupted (0 to 1) | 0.05 |
| Delay probability | Chance a packet or ACK gets 1 to 3 extra ticks of delay (0 to 1) | 0.1 |
| Timeout | Retransmission timeout, in channel ticks | 5 |

Time in the simulation is measured in ticks. One tick is 0.1 seconds of real time, and a packet normally takes 1 tick to cross the channel, so a 200-packet run takes at least about 10 seconds.

## The Results

```
python tests.py
```

This runs GBN and SR with 200 packets, N = 4 and k = 3 under three scenarios, each repeated 3 times and averaged:

- A: reliable channel (no loss, corruption or delay)
- B: loss 0.10
- C: loss 0.05, corruption 0.05, delay 0.10

It prints the results table (packets transmitted, retransmissions, packets delivered, completion time in ticks and seconds, and throughput in packets per tick).

## Notes
- Per-packet log lines are hidden during `tests.py` so that the table is readable. Run `main.py` to see the full log.