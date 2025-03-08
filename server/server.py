#!/usr/bin/env python3
import socket
import ssl
import os
import hashlib

def get_cert_fingerprint(cert_data):
    """Compute the SHA256 fingerprint of a certificate."""
    return hashlib.sha256(cert_data).hexdigest()

def is_client_whitelisted(cert_fingerprint, whitelist_file="whitelist.txt"):
    """Check if a client's certificate fingerprint is in the whitelist."""
    if not os.path.exists(whitelist_file):
        return False
    try:
        with open(whitelist_file, "r") as f:
            whitelisted_fingerprints = {line.strip() for line in f.readlines()}
        return cert_fingerprint in whitelisted_fingerprints
    except Exception as e:
        print(f"[ERROR] Failed to read {whitelist_file}: {e}")
        return False

def start_server():
    HOST = '127.0.0.1'
    PORT = 5000
    WHITELIST_FILE = "whitelist.txt"
    
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="server_cert.pem", keyfile="server_key.pem")
        context.verify_mode = ssl.CERT_NONE
    except Exception as e:
        print(f"[ERROR] Failed to set up TLS context: {e}")
        return
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        try:
            server_socket.bind((HOST, PORT))
            server_socket.listen(5)
            print(f"[INFO] Secure TLS server listening on {HOST}:{PORT}")
        except Exception as e:
            print(f"[ERROR] Failed to start server: {e}")
            return
        
        while True:
            try:
                conn, addr = server_socket.accept()
                with context.wrap_socket(conn, server_side=True) as tls_conn:
                    client_cert = tls_conn.getpeercert(binary_form=True) or b""
                    client_fingerprint = get_cert_fingerprint(client_cert)
                    
                    if is_client_whitelisted(client_fingerprint, WHITELIST_FILE):
                        print(f"[INFO] Accepted connection from whitelisted client {addr}")
                        tls_conn.sendall(b"Welcome, whitelisted client!\n")
                    else:
                        print(f"[WARNING] Client {addr} is not whitelisted. Fingerprint: {client_fingerprint}")
                        print(f"[INFO] To whitelist, add the following to {WHITELIST_FILE}: {client_fingerprint}")
                        tls_conn.close()
            except ssl.SSLError as e:
                print(f"[ERROR] SSL error during connection: {e}")
            except socket.error as e:
                print(f"[ERROR] Socket error: {e}")
            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")

if __name__ == "__main__":
    start_server()
