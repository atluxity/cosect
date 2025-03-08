#!/usr/bin/env python3
import socket
import ssl
import os
import hashlib

def get_cert_fingerprint(cert_data):
    """Compute the SHA256 fingerprint of a certificate."""
    return hashlib.sha256(cert_data).hexdigest()

def is_server_known(cert_fingerprint, known_servers_file="known_servers.txt"):
    """Check if the server's certificate fingerprint is known."""
    if not os.path.exists(known_servers_file):
        return False
    try:
        with open(known_servers_file, "r") as f:
            known_fingerprints = {line.strip() for line in f.readlines()}
        return cert_fingerprint in known_fingerprints
    except Exception as e:
        print(f"[ERROR] Failed to read {known_servers_file}: {e}")
        return False

def save_server_fingerprint(cert_fingerprint, known_servers_file="known_servers.txt"):
    """Save the server's fingerprint to the known servers list."""
    try:
        with open(known_servers_file, "a") as f:
            f.write(cert_fingerprint + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to save server fingerprint to {known_servers_file}: {e}")

def connect_to_server():
    HOST = "127.0.0.1"
    PORT = 5000
    
    try:
        context = ssl.create_default_context()
        context.load_cert_chain(certfile="client_cert.pem", keyfile="client_key.pem")
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    except Exception as e:
        print(f"[ERROR] Failed to set up TLS context: {e}")
        return
    
    try:
        with socket.create_connection((HOST, PORT)) as sock:
            with context.wrap_socket(sock, server_hostname=HOST) as tls_conn:
                server_cert = tls_conn.getpeercert(binary_form=True) or b""
                server_fingerprint = get_cert_fingerprint(server_cert)
                
                if not is_server_known(server_fingerprint):
                    confirm = input(f"[SECURITY] Unknown server fingerprint {server_fingerprint}. Trust this server? (yes/no): ")
                    if confirm.lower() == "yes":
                        save_server_fingerprint(server_fingerprint)
                    else:
                        print("[SECURITY] Connection rejected by user.")
                        return
                
                print("[INFO] Connected securely to server.")
                response = tls_conn.recv(1024)
                print(response.decode())
    except socket.error as e:
        print(f"[ERROR] Socket error while connecting to server: {e}")
    except ssl.SSLError as e:
        print(f"[ERROR] SSL error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

if __name__ == "__main__":
    connect_to_server()

