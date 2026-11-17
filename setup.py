import os
import requests
from urllib.parse import urlparse, parse_qs
from dotenv import set_key
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAGetAccountListByAccessTokenReq
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOAPayloadType
from twisted.internet import reactor

print("\n--- SETUP SCRIPT ---")
CLIENT_ID = input("Paste your cTrader Client ID here and press Enter: ").strip()
SECRET = input("Paste your cTrader Secret here and press Enter: ").strip()

set_key(".env", "CTRADER_CLIENT_ID", CLIENT_ID)
set_key(".env", "CTRADER_SECRET", SECRET)

REDIRECT_URI = "http://localhost"

print("\n--- STEP 1: GET AUTH CODE ---")
url = f"https://id.ctrader.com/my/settings/openapi/grantingaccess/?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=accounts"
print(f"1. Open this link in your browser:\n\n{url}\n")
print("2. Click 'Allow'.")
print("3. You will land on an error page (this is normal). COPY the entire URL from the address bar.")
pasted_url = input("\n4. Paste the URL here and press Enter: ").strip()

code = parse_qs(urlparse(pasted_url).query).get('code', [''])[0]
if not code:
    print("Could not find code in URL. Please try again.")
    exit()

print("\n--- STEP 2: GET TOKEN ---")
res = requests.post("https://openapi.ctrader.com/apps/token", data={
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": SECRET
}).json()

token = res.get("accessToken")
if not token:
    print("Error getting token:", res)
    exit()
    
print("Token received!")
set_key(".env", "CTRADER_ACCESS_TOKEN", token)

print("\n--- STEP 3: FIND ACCOUNT ID ---")
def on_connected(client):
    req = ProtoOAApplicationAuthReq()
    req.clientId = CLIENT_ID
    req.clientSecret = SECRET
    client.send(req)

def on_message(client, message):
    if message.payloadType == ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES:
        req = ProtoOAGetAccountListByAccessTokenReq()
        req.accessToken = token
        client.send(req)
    elif message.payloadType == ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES:
        extracted = Protobuf.extract(message)
        if len(extracted.ctidTraderAccount) == 0:
            print("No accounts found.")
            reactor.stop()
            return
        
        acc_id = extracted.ctidTraderAccount[0].ctidTraderAccountId
        print(f"Found Account ID: {acc_id}")
        set_key(".env", "CTRADER_ACCOUNT_ID", str(acc_id))
        print("Saved Account ID to .env")
        reactor.stop()

client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
client.setConnectedCallback(on_connected)
client.setMessageReceivedCallback(on_message)
client.startService()
reactor.run()
print("\nSetup complete! You can now run: python main.py")