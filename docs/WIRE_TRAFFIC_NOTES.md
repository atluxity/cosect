# Wire Traffic Notes

BLUF: the distributed demo shows real peer-to-peer PSI-related traffic on the wire. A simple first pass did not reveal the test domains as plain strings. A closer look showed the overlap values in a broadcast packet as base64-encoded strings. The current demo also exposes transport and runtime metadata because it does not enable TLS.

## Test Setup

The packet capture described here was taken during a small distributed run with:

- Party A: `apple.com`, `bbc.com`, `example.org`
- Party B: `bbc.com`, `example.org`, `paypal.com`

Expected intersection:

- `bbc.com`
- `example.org`

The capture was taken on loopback with `tcpdump` while [distributed_network_poc.py](/home/atluxity/git/cosect/distributed_network_poc.py) was running.

## What Was Visible

| Packet clue | Plain-English meaning | What it leaks | What it does not leak |
|---|---|---|---|
| `PRI * HTTP/2.0` | A gRPC-over-HTTP2 connection is starting | That the transport is plain gRPC/HTTP2 | Any domain values |
| `/SfFedProxy/SendData` | The party worker is calling a send-data RPC | Service/method name | The actual CSV rows |
| `application/grpc` | This channel uses gRPC payload framing | Application protocol choice | The PSI inputs themselves |
| `grpc-python/1.56.2` | Python gRPC client/runtime is in use | Client/runtime metadata | Any matching domains |
| `party_a` / `party_b` | The message identifies which side is speaking | Party identity labels | The other side's non-matching values |
| `original_count` | The sender is exposing how many items it started with | Input row counts | The actual item contents |
| `intersection_count` | The sender is exposing the result size | Overlap size | Which concrete items overlap, unless known elsewhere |
| `psi-tcpdump-demo` | The job id is present in metadata | Run/job identifier | Domain strings |
| `PRPC` | Lower-level protocol/runtime messages are being exchanged | That a custom RPC/runtime layer is active | The raw PSI data values |
| `org.interconnection.link.ReceiverService` | The distributed runtime is using a receiver service | Internal service name | Any domains |
| `Push` | One side is pushing protocol/runtime data to the other | Message direction and style | Plaintext list contents |
| `connect_0`, `connect_1` | Logical channels are being established | Link setup structure | Domain values |
| `root:1:ALLGATHER` / `root:2:ALLGATHER` | A collective synchronization step is happening | Runtime phase names | Raw participant inputs |
| `root:P2P-1:0->1` | A direct peer-to-peer transfer is happening | Which direction a runtime step moves | Plaintext domains |
| `ACK` | A chunk or phase was received and acknowledged | Stepwise progress | Any meaningful input content |
| Many medium/large binary payloads | Protocol/runtime data is moving | Timing and approximate message sizes | Human-readable domain strings |
| No `apple.com`, `bbc.com`, `example.org`, `paypal.com` in a simple `strings` pass | The test domains were absent as plain text strings | Very little by itself | Whether the values were encoded in another readable form |
| `root:8:BCAST` with `YmJjLmNvbQ==` and `ZXhhbXBsZS5vcmc=` | A broadcast step carried base64-encoded overlap values | The intersection values themselves, if the observer inspects and decodes the packet | The non-overlapping values from either side |

## What This Capture Shows

- The two sides are genuinely exchanging network traffic during the PSI run.
- The traffic includes a readable control plane and a more opaque data plane.
- The test domains were not visible as plaintext strings in the capture.
- The overlap values were visible in at least one broadcast packet as base64-encoded strings.
- The run reflects real network activity, not a fabricated transcript.

## What This Capture Does Not Show

- Packet inspection alone does not prove the full KKRT PSI math.
- It leaves open what a malicious host could inspect locally before or after the wire step.
- It does not rule out side-channel leakage.
- It says nothing about transport confidentiality, because the current demo traffic is not TLS-protected.

## Practical Interpretation

For the current demo, the wire picture is:

1. gRPC control channels come up between the party workers.
2. Runtime metadata and small control messages are exchanged.
3. Lower-level PRPC/SPU links are established.
4. Collective and peer-to-peer runtime phases run, such as `ALLGATHER` and `P2P`.
5. Binary payloads move during the PSI phase.
6. Acknowledgements and shutdown follow.

This is consistent with a real distributed PSI execution. It also shows that "the domains are not visible in plaintext" is a much narrower statement than "the wire traffic reveals nothing useful."

## Phase-By-Phase Timeline

| Phase | Packet clues | What is happening | What leaks |
|---|---|---|---|
| 1. Link setup | `connect_0`, `connect_1` | The lower-level PRPC/SPU links are being established between the two sides | Link structure and connection sequencing |
| 2. Early sync | `root:1:ALLGATHER`, `root:2:ALLGATHER` | Initial collective coordination steps | Phase names and timing |
| 3. First directed exchange | `root:P2P-1:0->1`, `root:P2P-1:1->0` | Direct point-to-point transfers begin | Direction of message flow and relative payload size |
| 4. More collectives | `root-0:1:ALLGATHER`, `root:4:ALLGATHER`, `root:5:ALLGATHER`, `root:6:ALLGATHER` | Additional synchronization or distributed compute coordination rounds | More runtime structure and sequencing |
| 5. Main peer exchanges | `root:P2P-2:*`, `root:P2P-3:*`, `root:P2P-4:*`, `root:P2P-5:*`, `root:P2P-6:*`, `root:P2P-7:*`, `root:P2P-8:*`, `root:P2P-9:*`, `root:P2P-10:*` | The bulk of the pairwise runtime traffic happens here | Message directions, number of rounds, packet sizes |
| 6. Late sync / finish | `root-1:1:ALLGATHER`, `p_finished`, `root:7:ALLGATHER` | Final coordination before result distribution | End-of-compute phase names |
| 7. Result distribution | `root:8:BCAST` | The result is broadcast | The intersection values themselves, in base64 form |
| 8. Acknowledgement / close | many `ACK` packets, then TCP `FIN` | Each phase is confirmed and the channels shut down | That the run completed and when it ended |

## What The Timeline Suggests

- The capture has a structured distributed-runtime workflow.
- The run alternates between collective phases such as `ALLGATHER` and direct phases such as `P2P`.
- The final overlap is distributed in a distinct broadcast step.
- The control plane and the computation/data plane are both visible in a non-TLS capture.

In the observed run, the most sensitive readable value-bearing packet was the `root:8:BCAST` step, which carried base64-encoded strings that decoded to:

- `bbc.com`
- `example.org`

## Security Implication

The current non-TLS distributed demo keeps the domain values out of obvious plaintext exposure on the wire, while still leaking metadata such as:

- party identity labels
- job id
- input counts
- intersection count
- service and runtime method names
- protocol phase names

Deeper inspection also showed that at least one result broadcast packet carried the intersection values in base64 form. In the observed test run, those values decoded to:

- `bbc.com`
- `example.org`

If reducing wire-visible metadata matters, the next step is to enable TLS for the distributed transport and repeat the same capture comparison.

## Canary Comparison

Two additional captures were taken with small canary inputs to see whether unique non-overlap values would appear in readable payloads.

Run 1 used:

- Party A only: `a-only-canary-001.example`
- Party B only: `b-only-canary-001.example`
- Shared value: `shared-canary-001.example`

Run 2 used:

- Party A only: `a-only-canary-002.example`
- Party B only: `b-only-canary-002.example`
- Shared value: `shared-canary-002.example`

In both captures, the readable result-bearing packet was again the `root:8:BCAST` step.

Observed broadcast values:

- Run 1: `c2hhcmVkLWNhbmFyeS0wMDEuZXhhbXBsZQ==` -> `shared-canary-001.example`
- Run 2: `c2hhcmVkLWNhbmFyeS0wMDIuZXhhbXBsZQ==` -> `shared-canary-002.example`

The unique canaries did not appear in the readable or base64-decoded payloads that were extracted from the captures:

- `a-only-canary-001.example`
- `b-only-canary-001.example`
- `a-only-canary-002.example`
- `b-only-canary-002.example`

This does not prove that unique input values never cross the wire in opaque binary form. It does strengthen the case that the readable value-bearing traffic is dominated by the final overlap rather than the full input lists.
