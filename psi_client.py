import base64
import requests
from private_set_intersection.python import client
from private_set_intersection.python import ServerSetup, Response, Request, server, DataStructure

CLIENT_ITEMS = ["foo.com", "hello.com", "baz.net"]
SERVER_URL = "https://localhost:5000/psi"
RESPONSE_URL = "https://localhost:5000/client_response"
reveal_intersection = True

print("🔧 PSI CLIENT STARTED")
print(f"🌐 Will send POST request to: {SERVER_URL}")
print(f"📨 Client items: {CLIENT_ITEMS}")

# Create PSI client
c = client.CreateWithNewKey(reveal_intersection)
key_bytes = client.GetPrivateKeyBytes(c)
print(f"🔑 Client private key ({len(key_bytes)} bytes): {key_bytes.hex()}")

# Send initial request
client_request = client.CreateRequest(c, CLIENT_ITEMS)
client_request_bytes = client_request.SerializeToString()
request_b64 = base64.b64encode(client_request_bytes).decode()

print("🔒 Encrypted client elements:")
for i, elem in enumerate(client_request.encrypted_elements):
    print(f"  [{i}] {elem.hex()}")

print("\n🌐 Sending PSI request...")
resp = requests.post(SERVER_URL, json={"client_request": request_b64}, verify=False)
if resp.status_code != 200:
    print(f"❌ Error: {resp.status_code}")
    exit(1)

data = resp.json()
server_setup_bytes = base64.b64decode(data["server_setup"])
server_response_bytes = base64.b64decode(data["server_response"])
server_request_bytes = base64.b64decode(data["server_request"])

# Deserialize
setup = ServerSetup()
setup.ParseFromString(server_setup_bytes)
response = Response()
response.ParseFromString(server_response_bytes)
intersection = client.GetIntersection(c, setup, response)
intersection_values = [CLIENT_ITEMS[i] for i in intersection]
print(f"✅ INTERSECTION (client): {intersection_values}")

# Re-encrypt server's encrypted elements
server_req = Request()
server_req.ParseFromString(server_request_bytes)
reencrypted = []
for i, e in enumerate(server_req.encrypted_elements):
    r = c.ReEncrypt(e)
    print(f"🔁 Re-encrypted server element [{i}]: {r.hex()}")
    reencrypted.append(r)

# Send re-encrypted list back to server
encoded = [base64.b64encode(x).decode() for x in reencrypted]
print("\n📡 Sending re-encrypted elements back to server...")
resp = requests.post(RESPONSE_URL, json={"reencrypted_server_items": encoded}, verify=False)
print(f"🧾 Server says: {resp.status_code} - {resp.text}")

