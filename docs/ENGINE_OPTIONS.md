# Engine Options

## BLUF

This repository currently supports two backends:

- SecretFlow
- OpenMined PSI

SecretFlow remains the heavier backend.

OpenMined PSI is now implemented as the lighter asymmetric alternative.

## What We Need From A Backend

For this repository, a replacement engine needs to support:

- two-party PSI
- party-local plaintext inputs
- direct network exchange between the parties
- a simple way to explain what crosses the wire
- a practical integration path from Python and Docker

The current operator model also expects:

- one local output per party
- one local receipt per party
- no centralized service staging both plaintext inputs

## SecretFlow

Why it stays in the repo for now:

- it already works end to end
- it matches the current trust boundary
- it has open source code, public docs, and an active upstream
- it comes from a larger privacy-compute ecosystem led by Ant Group

Why it is still uncomfortable:

- it is a large stack for a narrow PSI problem
- the implementation details are hard to stand behind without leaning on the upstream project
- the upstream trust story is tied to Ant Group and the wider SecretFlow ecosystem

Due-diligence note:

- [SECRETFLOW_DUE_DILIGENCE.md](SECRETFLOW_DUE_DILIGENCE.md)

## OpenMined PSI

Why it looks promising:

- it is a narrower PSI library rather than a broad privacy-compute platform
- the protocol story is easier to explain
- the project is easier to describe to a skeptical reader than a larger SPU-based stack
- it comes from the OpenMined open-source ecosystem rather than a larger vendor platform

What changed in this repository to support it:

- the API shape is client/server rather than the current SecretFlow peer runner
- Party A acts as server in the distributed demo
- Party B acts as client and learns the intersection first
- Party B then returns the final intersection so both sides end with matching output files and receipts

What is still rough:

- the distributed OpenMined demo currently uses local Python worker processes rather than Docker containers
- TLS is not implemented for the OpenMined transport in this repository
- the asymmetric flow is a little less intuitive than the SecretFlow mutual-output path

Due-diligence note:

- [OPENMINED_DUE_DILIGENCE.md](OPENMINED_DUE_DILIGENCE.md)

## Secondary Candidate: Microsoft APSI

Why it is interesting:

- it is a serious open-source PSI project
- it is narrower in scope than SecretFlow
- it comes from Microsoft, which some audiences may find easier to stand behind institutionally than either Ant Group or a smaller non-profit ecosystem

Why it is a weaker fit for this repository:

- APSI is asymmetric by design
- that is less natural for the current "both sides end with the same intersection" story
- it is more naturally a C++ library and CLI integration project than a lightweight Python adapter
- integrating it would likely change the operator story more than OpenMined PSI would

Feasibility note:

- [APSI_FEASIBILITY.md](APSI_FEASIBILITY.md)

## Practical Recommendation

Keep both backends available.

Use SecretFlow when you want the current distributed stack with the existing packet-capture and due-diligence work.

Use OpenMined when you want a smaller dependency and a simpler story about what cryptographic building blocks are in use.

## Short Comparison

For this repository, the two engines are close in business outcome and different in shape.

- SecretFlow is the more naturally symmetric path. Both parties get the result as part of the engine's own flow.
- OpenMined is asymmetric. In this repository, Party B learns the result first and then sends it back so both sides end with the same output file and receipt.
- SecretFlow has the heavier runtime and dependency footprint.
- OpenMined has the smaller and easier-to-explain code surface.
- SecretFlow is associated with Ant Group and a broader industrial privacy-compute stack.
- OpenMined PSI is associated with the OpenMined non-profit open-source ecosystem and a narrower PSI library surface.

So the difference is not "one works and one does not." The real difference is:

- symmetric engine flow versus asymmetric engine flow
- heavier stack versus lighter library
- different upstream organizations and trust choices

## Geopolitical Context

Some audiences will care about the upstream organizations in a geopolitical sense, not just a technical one.

- SecretFlow is part of an ecosystem led by Ant Group, a large Chinese technology and financial-services company based in Hangzhou.
- OpenMined PSI comes from the OpenMined ecosystem, a 501(c)(3) non-profit open-source organization with a public-good framing and a more Western non-profit institutional profile.

That does not settle the technical question by itself.

It does change the non-technical trust discussion:

- vendor-backed Chinese industrial platform versus non-profit open-source community
- larger corporate ecosystem versus narrower public-interest ecosystem
- different legal, regulatory, and reputational environments around the upstreams

For some stakeholders, that difference will matter as much as protocol shape or runtime complexity.
