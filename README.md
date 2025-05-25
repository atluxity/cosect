# cosect

Status: Future-ware, ambitions defined.

Cosect is a privacy-preserving tool using Private Set Intersection (PSI) to allow two trusted parties to securely and efficiently identify overlapping data (such as observables like domains, hashes, or IPs) without exposing their full datasets.

## Use Case

Cosect is ideal for scenarios where two parties:

* Trust each other's intentions but cannot or do not want to share their entire dataset.
* Need to check for overlaps in sensitive information like:

  * Customer lists
  * Threat intelligence observables (domains, IPs, hashes, etc.)

## Roadmap

* [x] Define ambitions and scope
* [x] Define technical approach for PSI
* [x] Review OpenMined PSI and Google Private Join and Compute
* [ ] Implement proof-of-concept client-server model using Flask + mTLS
* [ ] Implement commutative encryption PSI flow using OpenMined library
* [ ] Add CLI utility support for client/server testing
* [ ] Improve usability (better CLI options, integration support)
* [ ] Explore API or plugin-based extensions
* [ ] Add test cases and validation
* [ ] Improve documentation and usability

## Cosect Project Scope

### **1. Project Overview**

Cosect is a privacy-preserving tool designed to enable two parties with an existing but limited trust level to securely identify overlapping data (such as threat intelligence observables) without exposing their full datasets. It leverages **Private Set Intersection (PSI)** to ensure only necessary data is shared while maintaining strong encryption.

### **2. Problem Statement**

In cybersecurity and threat intelligence sharing, two well-intentioned parties often face the challenge of needing to compare sensitive data while minimizing data exposure. Currently, the available solutions either:

* Require sharing full datasets, which is often unacceptable.
* Use simple hashing methods that do not provide true anonymity.
* Lack user-friendly and efficient implementation for real-world usage.

Cosect aims to fill this gap by providing an easy-to-use tool that ensures **privacy-first data sharing** using proper cryptographic PSI methods.

### **3. Target Users & Use Cases**

#### **Primary Users:**

* SOC analysts, CTI professionals, MSSPs, IT security teams
* Researchers or investigative teams handling sensitive information

#### **Example Use Cases:**

1. **Threat Intelligence Sharing**: One party has a list of **compromised domains**, the other has a list of **customer domains**. Both want to know if any compromised domains belong to customers **without revealing full datasets**.
2. **Fraud Detection**: Financial institutions comparing fraud indicators.
3. **Privacy-Preserving Collaboration**: Organizations checking for shared indicators of compromise or breach info.

### **4. Privacy & Security Considerations**

* **Data Exposure Policy**: Only overlapping data is revealed to both parties.
* **Metadata Leakage**: Parties may pad datasets with dummy values.
* **Trust Model**: Assumes semi-honest model; both sides follow protocol but want to learn nothing more than the intersection.
* **Fresh Keys**: Each PSI run uses newly generated keys to prevent set reconstruction over time.
* **Misuse Risk**: Small input size (∼10³) makes mass exploitation detectable through monitoring/reporting.

### **5. Supported Data Types**

Cosect processes simple **lists of strings**, including:

* Domains, IPs, file hashes
* (Future) emails, usernames, transaction IDs

### **6. Minimal Viable Product (MVP)**

#### **Scope of First Release:**

* Client-server architecture with encrypted PSI comparison
* Use of OpenMined PSI library with commutative encryption
* Flask-based REST API with optional mTLS
* CLI client/server for testing
* Standard input/output via files or pipes

### **7. Cryptographic & Technical Approach**

* **Encryption**: Elliptic Curve Diffie-Hellman (ECDH)-style commutative encryption
* **Hashing**: SHA-256 pre-hashing for fixed-size domain mapping
* **PSI Logic**:

  * Alice: hashes and encrypts each item with key x
  * Bob: hashes and encrypts each item with key y
  * Both sides re-encrypt the other's data with their own key
  * If `Enc_y(Enc_x(u)) == Enc_x(Enc_y(u))`, the item is in the intersection
* **Library**: [OpenMined/PSI](https://github.com/OpenMined/PSI) Python wrapper
* **Compression**: Not needed for \~1000 elements; future optional use of Bloom filters or Golomb-Compressed Sets

### **8. Implementation Details**

* Flask REST endpoint `/psi` accepts serialized client request
* Server generates setup + response using OpenMined PSI
* Client uses `GetIntersection()` to compute matching elements
* CLI script for both client/server interaction

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

Cosect is licensed under the [Apache 2.0 License](LICENSE).

## Disclaimer

Cosect is developed as a learning project and is not production-ready. Use at your own risk.

## Acknowledgments

This project was inspired by the need for secure and private data sharing in collaborative environments like FIRST.org and Team Norway.
