# cosect

Status: Future-ware, ambitions defined.

Cosect is a privacy-preserving tool using Private Set Intersection (PSI) in order to allow two trusted parties to securely and efficiently identify overlapping data (such as observables like domains, hashes, or IPs) without exposing their full datasets.

## Use Case
Cosect is ideal for scenarios where two parties:
- Trust each other's intentions but cannot or do not want to share their entire dataset.
- Need to check for overlaps in sensitive information like:
  - Customer lists
  - Threat intelligence observables (domains, IPs, hashes, etc.)

## Roadmap
- [x] Define ambitions and scope
- [ ] Define technical approach for PSI.
- [ ] Develop proof-of-concept client-server model.
- [ ] Implement encryption and authentication.
- [ ] Implement PSI
- [ ] Improve usability (better CLI options, integration support).
- [ ] Explore API or plugin-based extensions.
- [ ] Add test cases and validation.
- [ ] Improve documentation and usability.

## Cosect Project Scope

### **1. Project Overview**
Cosect is a privacy-preserving tool designed to enable two parties with an existing but limited trust level to securely identify overlapping data (such as threat intelligence observables) without exposing their full datasets. It leverages **Private Set Intersection (PSI)** to ensure only necessary data is shared while maintaining strong encryption.

### **2. Problem Statement**
In cybersecurity and threat intelligence sharing, two well-intentioned parties often face the challenge of needing to compare sensitive data while minimizing data exposure. Currently, the available solutions either:
- Require sharing full datasets, which is often unacceptable.
- Use simple hashing methods that do not provide true anonymity.
- Lack user-friendly and efficient implementation for real-world usage.

Cosect aims to fill this gap by providing an easy-to-use tool that ensures **privacy-first data sharing** using proper cryptographic PSI methods.

### **3. Target Users & Use Cases**
#### **Primary Users:**
- SOC analysts, CTI professionals, MSSPs, IT security teams.
- Researchers or investigative teams handling sensitive information.

#### **Example Use Case:**
1. **Threat Intelligence Sharing**: One party has a list of **compromised domains** obtained via threat actor monitoring, while the other party has a list of **customer domains**. Both want to know if any compromised domains belong to customers **without revealing their entire datasets**.
2. **Fraud Detection**: Financial institutions comparing customer fraud reports.
3. **Privacy-Preserving Collaboration**: Organizations checking for shared breaches or indicators of compromise.

### **4. Privacy & Security Considerations**
- **Data Exposure Policy:** Only overlapping data is revealed to both parties.
- **Metadata Leakage:** Parties may pad their dataset with dummy values to obscure actual dataset size.
- **Trust Model:** Cosect assumes a semi-trusted environment where parties have an agreement in place but still require technical safeguards.
- **Adversarial Behavior:** Malicious behavior is discouraged through external agreements and consequences.

### **5. Supported Data Types**
Cosect will process simple **lists of strings**, including:
- **Threat Intelligence Observables**: Domains, IPs, file hashes.
- **Other Use Cases (Future Consideration)**: Emails, usernames, transaction IDs.

### **6. Minimal Viable Product (MVP)**
#### **Scope of First Release:**
- Command-line utility with **client-server architecture**.
- PSI-based comparison over **encrypted TCP connection**.
- Mutual authentication to ensure parties’ identities.
- Input/output via standard pipes or files.

### **7. Cryptographic & Security Considerations**
- **Cryptographic PSI Methods:** TBD after further consultation.
- **Basic Requirement:** Must offer stronger privacy than simple hashing (SHA-256, Bloom filters, etc.).
- **Encryption & Authentication:** Mandatory encryption and mutual authentication for secure data transmission.

---
Cosect is an evolving project aimed at solving a real-world **privacy-preserving data-sharing challenge**. Contributions and feedback are welcome to refine its scope and implementation!

## Setting Up TLS Certificates for Cosect

Cosect uses **TLS encryption** to secure communication between the client and server. Before running the server and client, you need to generate the necessary certificates and set up mutual authentication.

### **1. Generating Self-Signed Certificates**
To generate a **self-signed certificate** and private key for both server and client, run:

```bash
# Generate server private key and certificate
openssl req -new -x509 -days 365 -nodes -out server_cert.pem -keyout server_key.pem   -subj "/CN=Cosect Server"

# Generate client private key and certificate
openssl req -new -x509 -days 365 -nodes -out client_cert.pem -keyout client_key.pem   -subj "/CN=Cosect Client"
```

### **2. Creating a Certificate Authority (Optional)**
For better security, you can create a **Certificate Authority (CA)** and sign the certificates:

```bash
# Create a CA key and certificate
openssl req -new -x509 -days 365 -nodes -out ca_cert.pem -keyout ca_key.pem   -subj "/CN=Cosect CA"

# Generate server certificate signing request (CSR)
openssl req -new -nodes -out server.csr -keyout server_key.pem   -subj "/CN=Cosect Server"

# Sign the server certificate with the CA
openssl x509 -req -in server.csr -CA ca_cert.pem -CAkey ca_key.pem -CAcreateserial   -out server_cert.pem -days 365

# Generate client certificate signing request (CSR)
openssl req -new -nodes -out client.csr -keyout client_key.pem   -subj "/CN=Cosect Client"

# Sign the client certificate with the CA
openssl x509 -req -in client.csr -CA ca_cert.pem -CAkey ca_key.pem -CAcreateserial   -out client_cert.pem -days 365
```

### **3. Configuring the Server**
Place the following files in the server’s working directory:
- `server_cert.pem` (Server certificate)
- `server_key.pem` (Server private key)
- `ca_cert.pem` (CA certificate, if using a CA)
- `whitelist.txt` (List of allowed client certificate fingerprints, one per line)

Then, start the server:

```bash
python server.py --cert server_cert.pem --key server_key.pem --ca ca_cert.pem
```

### **4. Configuring the Client**
Place the following files in the client's working directory:
- `client_cert.pem` (Client certificate)
- `client_key.pem` (Client private key)
- `ca_cert.pem` (CA certificate, if using a CA)

Then, connect the client to the server:

```bash
python client.py --cert client_cert.pem --key client_key.pem --ca ca_cert.pem --server <server_address>
```

### **5. Verifying TLS Connection**
To verify that the certificates are valid and working, run:

```bash
openssl s_client -connect <server_address>:<port> -CAfile ca_cert.pem -cert client_cert.pem -key client_key.pem
```

This should establish a secure connection without certificate errors.

---

## Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.

## License
Cosect is licensed under the [Apache 2.0 License](LICENSE).

## Disclaimer
Cosect is developed as a learning project and is not production-ready. Use at your own risk.

## Acknowledgments
This project was inspired by the need for secure and private data sharing in collaborative environments like FIRST.org and Team Norway.
