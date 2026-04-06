# SecretFlow Due Diligence

## BLUF

We use SecretFlow as the PSI engine in this repository.

We are not re-proving its cryptography here.

What we can do is separate two questions:

- is SecretFlow a real and inspectable upstream project
- are we integrating it in a way that obviously defeats the privacy goal

The answer to the first question is yes, with limits.

The answer to the second question is also yes, based on the work documented in this repository.

## Scope

This note is about trust signals and integration checks.

It is not a formal audit.

It does not claim to establish that SecretFlow PSI is free of bugs, side channels, or design mistakes.

## Who Is Behind SecretFlow

SecretFlow is an open-source project led by Ant Group.

Useful public signals:

- the `secretflow` GitHub organization is verified and tied to `service.alipay.com`
- Ant Group's verified GitHub organization lists SecretFlow among its projects
- Ant Group publicly describes SecretFlow as one of its privacy-preserving computing efforts

Reference points:

- `https://github.com/secretflow`
- `https://github.com/antgroup`
- `https://www.antgroup.com/`

## What Is Publicly Available

The project is not a black box.

Publicly available material includes:

- SecretFlow framework source code
- SecretFlow PSI library source code
- SecretFlow documentation for PSI and deployment
- lower-level related repositories such as `spu` and `yacl`

Main source locations:

- `https://github.com/secretflow/secretflow`
- `https://github.com/secretflow/psi`
- `https://secretflow.readthedocs.io/en/stable/user_guide/psi.html`
- `https://secretflow.readthedocs.io/en/stable/getting_started/deployment.html`
- `https://secretflow.readthedocs.io/en/stable/tutorial/PSI_On_SPU.html`

## External Trust Signals

There are some useful outside signals.

- SecretFlow-SPU has a USENIX ATC 2023 paper:
  `https://www.usenix.org/conference/atc23/presentation/ma`
- the public GitHub repos are active and have non-trivial community activity
- the project has tagged releases, issues, forks, and contributors visible in public

These are meaningful signals of technical seriousness.

They are not the same as an independent security audit of SecretFlow PSI.

## What We Did Not Find

We did not find clear public evidence of a named third-party security audit focused on SecretFlow PSI itself.

That absence matters.

It means our trust judgment should be:

- stronger than "we have no idea who wrote this"
- weaker than "an independent lab has signed off on this implementation"

## What We Checked Ourselves

We focused on the part we control: the surrounding integration.

### 1. Plaintext Handling

We removed the old centralized flow where one side could upload a plaintext CSV to infrastructure controlled by the other side.

The remaining remote path keeps:

- Party A plaintext on Party A's side
- Party B plaintext on Party B's side
- only session metadata and PSI traffic crossing the network

Relevant code paths:

- `run_2party_psi_peer.py`
- `distributed_network_poc.py`
- `write_peer_psi_session.py`

### 2. Receipt Consistency

Each party writes a local receipt containing:

- session hash
- local input hash
- local output hash
- output row count
- engine and protocol metadata

`verify_peer_psi_receipts.py` checks that both sides agree on the same session and output.

### 3. Packet-Capture Inspection

We captured and inspected network traffic during the distributed demo.

That work is summarized in `docs/WIRE_TRAFFIC_NOTES.md`.

What we observed:

- real peer-to-peer traffic during PSI
- visible control metadata on the wire in the non-TLS demo
- visible overlap values during result broadcast in the non-TLS demo
- no full Party A or Party B input lists in the readable parts of the captures we inspected

### 4. Canary Runs

We ran packet captures with unique canary domains on each side and one shared canary.

What we found:

- the shared canary appeared in the result broadcast, as expected
- the A-only and B-only canaries did not appear in the readable payloads we extracted

That is not a proof that unique values never cross the wire in any encoded form.

It is still useful evidence that our integration is not leaking the full lists in an obvious or careless way.

## What We Are Actually Claiming

The right claim is narrow.

We trust SecretFlow to implement PSI correctly.

What this repository adds is evidence that our own wrapper and demo wiring do not obviously break that property by:

- staging both plaintext inputs on one host
- sending raw CSV rows in readable form across the network
- losing track of which local inputs produced which outputs

## What We Are Not Claiming

We are not claiming:

- a formal audit of SecretFlow PSI
- proof that no side channel or opaque-payload leakage exists
- proof that host machines were honest or untampered
- proof that the current non-TLS demo hides metadata from a network observer

## Current Bottom Line

As of 2026-04-06, the practical trust position for this repository is:

- SecretFlow is an open and inspectable upstream, led by a known organization
- public signals suggest a serious engineering project
- we did not find a public independent audit of SecretFlow PSI
- our own integration work keeps each party's plaintext local
- our own packet-capture and canary checks did not show the full input lists in the readable parts of network traffic

That is enough to stand behind the integration story.

It is not enough to claim independent verification of the SecretFlow cryptography itself.
