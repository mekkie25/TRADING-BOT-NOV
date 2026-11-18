import os
from dotenv import load_dotenv

# 1. Load the .env file
load_dotenv()

# 2. Read the variables
client_id = os.getenv("CTRADER_CLIENT_ID")
client_secret = os.getenv("CTRADER_CLIENT_SECRET")
access_token = os.getenv("CTRADER_ACCESS_TOKEN")
account_id = os.getenv("CTRADER_ACCOUNT_ID")
env = os.getenv("CTRADER_ENV", "demo")

print("--- Environment Check ---")
if not client_id:
    print("❌ Error: CTRADER_CLIENT_ID is missing from .env")
else:
    print(f"✅ Client ID: {client_id[:4]}*** (Loaded successfully)")
    
if not access_token:
    print("❌ Error: CTRADER_ACCESS_TOKEN is missing from .env")
else:
    print(f"✅ Access Token: {access_token[:4]}*** (Loaded successfully)")
    
print(f"✅ Target Environment: {env.upper()}")

# 3. Initialize the cTrader Client
try:
    from ctrader_open_api import Client, EndPoints, TcpProtocol
    
    host = EndPoints.PROTOBUF_DEMO_HOST if env.lower() == "demo" else EndPoints.PROTOBUF_LIVE_HOST
    print(f"\nAttempting to connect to cTrader at {host}...")
    
    client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
    print("✅ Client created successfully! The cTrader library is ready.")
    
except ImportError:
    print("\n❌ Error: ctrader-open-api is not installed.")