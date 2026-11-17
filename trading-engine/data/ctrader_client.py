import os
import datetime
import pandas as pd
from dotenv import load_dotenv
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAAccountAuthReq, ProtoOASymbolsListReq,
    ProtoOAGetTrendbarsReq
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (
    ProtoOATrendbarPeriod,
    ProtoOAPayloadType
)
from twisted.internet import reactor

load_dotenv()

class CTraderClient:
    def __init__(self):
        self.client_id = os.getenv("CTRADER_CLIENT_ID")
        self.secret = os.getenv("CTRADER_SECRET")
        self.token = os.getenv("CTRADER_ACCESS_TOKEN")
        self.account_id = int(os.getenv("CTRADER_ACCOUNT_ID"))
        
        # SWITCHED TO LIVE HOST FOR DATA STABILITY
        self.client = Client(EndPoints.PROTOBUF_LIVE_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
        self.client.setConnectedCallback(self.on_connected)
        self.client.setMessageReceivedCallback(self.on_message)
        
        self.target_symbol = "EURUSD"
        self.symbol_id = None

    def on_connected(self, client):
        print("Connected to cTrader LIVE API...")
        req = ProtoOAApplicationAuthReq()
        req.clientId = self.client_id
        req.clientSecret = self.secret
        client.send(req)

    def on_message(self, client, message):
        if message.payloadType == ProtoOAPayloadType.PROTO_OA_ERROR_RES:
            err = Protobuf.extract(message)
            print("\n!!! cTrader Error:", err.description)
            reactor.stop()
            return

        if message.payloadType == ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES:
            print("App Authenticated. Authenticating Account...")
            req = ProtoOAAccountAuthReq()
            req.ctidTraderAccountId = self.account_id
            req.accessToken = self.token
            client.send(req)

        elif message.payloadType == ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES:
            print("Account Authenticated. Fetching Symbol List...")
            req = ProtoOASymbolsListReq()
            req.ctidTraderAccountId = self.account_id
            client.send(req)

        elif message.payloadType == ProtoOAPayloadType.PROTO_OA_SYMBOLS_LIST_RES:
            res = Protobuf.extract(message)
            for symbol in res.symbol:
                if symbol.symbolName == self.target_symbol:
                    self.symbol_id = symbol.symbolId
                    break
            
            if not self.symbol_id:
                print(f"ERROR: Could not find {self.target_symbol} in symbol list.")
                reactor.stop()
                return

            print(f"Found {self.target_symbol} (ID: {self.symbol_id}). Fetching 1 year of H1 data...")
            
            req = ProtoOAGetTrendbarsReq()
            req.ctidTraderAccountId = self.account_id
            req.symbolId = self.symbol_id
            req.period = ProtoOATrendbarPeriod.H1
            
            end_time = datetime.datetime.now(datetime.timezone.utc)
            start_time = end_time - datetime.timedelta(days=365)
            req.fromTimestamp = int(start_time.timestamp() * 1000)
            req.toTimestamp = int(end_time.timestamp() * 1000)
            client.send(req)

        elif message.payloadType == ProtoOAPayloadType.PROTO_OA_GET_TRENDBARS_RES:
            res = Protobuf.extract(message)
            print(f"Trendbars received! Processing {len(res.trendbar)} bars...")
            bars = []
            for bar in res.trendbar:
                low = bar.low / 100000.0
                open_p = low + (bar.deltaOpen / 100000.0)
                high = low + (bar.deltaHigh / 100000.0)
                close = low + (bar.deltaClose / 100000.0)
                
                bars.append({
                    "timestamp": datetime.datetime.fromtimestamp(bar.utcTimestampInMinutes * 60, datetime.timezone.utc),
                    "open": open_p,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": bar.volume
                })
            
            df = pd.DataFrame(bars)
            df = df.sort_values("timestamp").reset_index(drop=True)
            
            os.makedirs("data", exist_ok=True)
            df.to_parquet(f"data/{self.target_symbol}_H1.parquet")
            
            print(f"Successfully saved {len(df)} bars to data/{self.target_symbol}_H1.parquet")
            reactor.stop()

    def fetch(self):
        print("Starting data fetch...")
        self.client.startService()
        reactor.run()

if __name__ == "__main__":
    client = CTraderClient()
    client.fetch()