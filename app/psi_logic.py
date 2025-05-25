import base64
from private_set_intersection.python import server, client as psi_client, DataStructure, Request

# Server-side items
_server_items = ["foo.com", "bar.com", "baz.net"]

# One client object: server acting as client
_server_client = psi_client.CreateWithNewKey(True)
_server_request = psi_client.CreateRequest(_server_client, _server_items)

# One server object: server acting as PSI responder
_server_server = server.CreateWithNewKey(True)

def simulate_server_response(client_request_bytes: bytes, server_items: list[str]) -> tuple[str, str, str]:
    print(f"🔐 SERVER: Received client request ({len(client_request_bytes)} bytes)")

    req = Request()
    req.ParseFromString(client_request_bytes)

    print(f"🔍 Parsed {len(req.encrypted_elements)} encrypted client elements:")
    for i, elem in enumerate(req.encrypted_elements):
        print(f"  [{i}] {elem.hex()}")

    # Process client request
    setup = _server_server.CreateSetupMessage(
        0.01, len(server_items), server_items, DataStructure.RAW
    )
    response = _server_server.ProcessRequest(req)

    server_request_bytes = _server_request.SerializeToString()

    print("📤 Server response generated.")
    return (
        base64.b64encode(setup.SerializeToString()).decode(),
        base64.b64encode(response.SerializeToString()).decode(),
        base64.b64encode(server_request_bytes).decode()
    )

def process_client_reencrypted(encoded_elements: list[str]) -> list[str]:
    received = [base64.b64decode(e) for e in encoded_elements]

    # Re-encrypt server's own encrypted items with its PSI responder key
    local_reencrypted = [
        psi_client.ReEncrypt(_server_client, enc_elem)
        for enc_elem in _server_request.encrypted_elements
    ]

    matched = []
    for i, val in enumerate(local_reencrypted):
        if val in received:
            matched.append(_server_items[i])

    print(f"✅ SERVER: Matched {len(matched)} items in client response: {matched}")
    return matched

