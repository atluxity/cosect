# OpenMined PSI Due Diligence

## BLUF

We use OpenMined PSI as the lighter alternative PSI engine in this repository.

We are not re-proving its cryptography here.

As with SecretFlow, the useful split is:

- is OpenMined PSI a real and inspectable upstream project
- are we integrating it in a way that obviously defeats the privacy goal

The answer to the first question is yes, with limits.

The answer to the second question is yes for the current repository integration, based on the checks described here.

## Scope

This note is about trust signals and integration checks.

It is not a formal audit.

It does not claim to establish that OpenMined PSI is free of bugs, side channels, or design mistakes.

## Who Is Behind OpenMined PSI

OpenMined PSI is part of the OpenMined open-source ecosystem.

For some readers, the important background fact is that this places the project in a very different institutional setting from SecretFlow: an open-source non-profit community rather than a large Chinese corporate platform.

Useful public signals:

- the `openmined` GitHub organization is verified
- the GitHub organization links to `openmined.org`
- OpenMined describes itself as a non-profit community building privacy-preserving and secure-computation technology

Reference points:

- `https://github.com/openmined`
- `https://github.com/OpenMined/PSI`
- `https://openmined.org/`

## What Is Publicly Available

The project is not a black box.

Publicly available material includes:

- the PSI repository source code
- Python bindings published to PyPI
- the repository README with protocol and security references
- project-level `SECURITY.md`

Main source locations:

- `https://github.com/OpenMined/PSI`
- `https://pypi.org/project/openmined-psi/`

## External Trust Signals

There are some useful outside signals.

- the project is under a known open-source organization rather than a personal repository
- the repository is public, Apache-2.0 licensed, and has tagged releases
- the Python package is publicly distributed through PyPI

These are meaningful signals of openness and maintainability.

They are not the same as an independent security audit of OpenMined PSI.

## What We Did Not Find

We did not find clear public evidence of a named third-party security audit focused on OpenMined PSI itself.

We also did not find the same level of packet-capture or deployment-oriented public documentation that exists around the current SecretFlow path in this repository.

That means our trust judgment should be:

- stronger than "we do not know what this package is"
- weaker than "an independent lab has signed off on this implementation"

## What We Checked Ourselves

We focused on the part we control: the surrounding integration.

### 1. API Surface

We installed the published Python package and inspected the actual Python bindings we are using.

The API we integrated is the one exposed by `private_set_intersection.python`:

- `client.CreateWithNewKey(...)`
- `server.CreateWithNewKey(...)`
- `CreateRequest(...)`
- `CreateSetupMessage(...)`
- `ProcessRequest(...)`
- `GetIntersection(...)`

That matters because the repository is wired against the real package interface, not against a guessed protocol wrapper.

### 2. Plaintext Handling

The OpenMined distributed path keeps the same hard boundary as the rest of the repository:

- Party A plaintext stays on Party A's side
- Party B plaintext stays on Party B's side
- only protocol messages, result-sharing messages, and session metadata cross the network

Relevant code paths:

- `openmined_backend.py`
- `run_2party_psi_peer.py`
- `distributed_network_poc.py`
- `write_peer_psi_session.py`

### 3. Result Handling

OpenMined PSI is asymmetric in the form we use here.

In the current distributed integration:

- Party A acts as the OpenMined server
- Party B acts as the OpenMined client
- Party B learns the intersection first
- Party B then sends the final intersection back to Party A

That is an explicit design choice in this repository so both sides end with the same output file and the same receipt structure.

### 4. Receipt Consistency

Each party writes a local receipt containing:

- session hash
- local input hash
- local output hash
- output row count
- engine and protocol metadata

`verify_peer_psi_receipts.py` checks that both sides agree on the same session and output.

### 5. End-to-End Runs

We verified both OpenMined entry points in this repository:

- standalone local run
- distributed two-process run

That gives us confidence that the engine works within the repository's actual operator flow rather than only as a toy library import.

### 6. Packet-Capture Inspection

We captured and inspected network traffic during the distributed OpenMined demo.

That work is summarized in `docs/OPENMINED_WIRE_TRAFFIC_NOTES.md`.

What we observed:

- real peer-to-peer traffic during PSI
- readable JSON wrapper messages on the wire
- the final overlap returned in clear JSON
- no full Party A or Party B input lists in the readable payloads we extracted

### 7. Canary Runs

We ran packet captures with unique canary domains on each side and one shared canary.

What we found:

- the shared canary appeared in the `intersection_rows` message, exactly as expected
- the A-only and B-only canaries did not appear in the readable payloads we extracted

That is not a proof that unique values never cross the wire in encoded form.

It is still useful evidence that the current wrapper is not exposing the full input lists in obvious readable form.

## What We Are Actually Claiming

The right claim is narrow.

We trust OpenMined PSI to implement its protocol correctly.

What this repository adds is evidence that our own wrapper and demo wiring do not obviously break that property by:

- staging both plaintext inputs on one host
- losing track of which local inputs produced which outputs
- leaving one side with a different result artifact than the other

## What We Are Not Claiming

We are not claiming:

- a formal audit of OpenMined PSI
- proof that no side channel or opaque-payload leakage exists
- proof that host machines were honest or untampered
- proof that the current local socket transport hides metadata from a network observer

## Current Bottom Line

As of 2026-04-06, the practical trust position for this repository is:

- OpenMined PSI is an open and inspectable upstream under a known open-source organization
- the published Python package matches the API used by this repository
- we did not find a public independent audit of OpenMined PSI
- our own integration work keeps each party's plaintext local
- our own end-to-end checks show that both parties still end with the same result and matching receipts
- our own packet captures show the final overlap on the wire, but not the full input lists in the readable payloads we extracted

That is enough to stand behind the integration story.

It is not enough to claim independent verification of the OpenMined cryptography itself.
