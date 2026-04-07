# APSI Feasibility

## BLUF

Microsoft APSI is still the next serious backend candidate after SecretFlow and OpenMined.

It is a credible PSI project, but it is not a quick drop-in for this repository.

The main reason is not cryptography. The main reason is integration shape:

- APSI is asymmetric
- APSI is centered on a C++ library and CLI
- APSI would require a different operator wrapper than either existing backend

## Why APSI Is Still Interesting

APSI has several properties that make it worth keeping on the shortlist:

- it is a Microsoft-backed open-source PSI project
- it is narrower in scope than SecretFlow
- it comes from a different upstream organization than both Ant Group and OpenMined
- it has a documented CLI and a documented library API

Useful public references:

- `https://github.com/microsoft/APSI`

## What The Upstream Looks Like

The APSI README describes it as a C++ library for asymmetric PSI.

The repository documents:

- a `Sender`
- a `Receiver`
- command-line sender and receiver programs
- TCP and ZeroMQ-style networking support
- sender-chosen parameters in the CLI flow

That already tells us APSI is closer in spirit to OpenMined than to SecretFlow:

- one side is a sender
- one side is a receiver
- the protocol is asymmetric by design

## What Fits This Repository Well

APSI matches several requirements of this repository:

- two-party PSI
- no need for centralized plaintext staging
- a serious open-source upstream
- a more bounded scope than a full privacy-compute platform

It also has one non-technical advantage for some audiences:

- the upstream organization is Microsoft rather than Ant Group or a non-profit open-source community

That may matter for readers who care about institutional trust and geopolitics.

## What Does Not Fit Cleanly

APSI does not fit the current repository as neatly as OpenMined.

The main issues are:

- asymmetric sender/receiver model
- C++-first integration surface
- more parameter-management burden
- no obvious lightweight Python package path comparable to `openmined-psi`

From the upstream README, the documented operational path is largely:

- build the APSI library
- optionally build the sender and receiver CLI
- provide parameter files and sender data
- run a sender endpoint and a receiver client

That means APSI would likely need a wrapper architecture based on:

- repo-managed CLI binaries, or
- a custom subprocess bridge around APSI sender and receiver programs

That is a bigger integration step than the OpenMined backend required.

## Likely Repository Shape If We Add APSI

If APSI is added, the repo would probably need:

- `engine=apsi` in session files and receipts
- an APSI sender wrapper
- an APSI receiver wrapper
- parameter-file handling
- a result-return step so both sides end with the same output file and receipt

That last step matters because APSI is asymmetric.

Just as with OpenMined, the repository would need to decide:

- which side learns the result first
- how the other side receives the final result artifact

## Practical Blockers Right Now

The main blockers are operational:

- no APSI backend is implemented here yet
- no APSI build pipeline exists in this repo
- no local binary management exists for APSI sender and receiver
- no packet-capture or canary work has been done for an APSI integration

This is not a statement that APSI is a bad fit.

It is a statement that APSI is the next substantial integration project, not a small patch.

## Recommendation

Keep APSI as the next backend candidate, not the immediate default.

If the project needs a third engine, APSI is the right next one to try.

But it should be approached as:

- a new integration track
- a wrapper-and-tooling project
- not just another small adapter module
