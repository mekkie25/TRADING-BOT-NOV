"""
Module: Live cTrader Data Feed
Purpose: Connects to cTrader Open API, authenticates, subscribes to live spots and M5 trendbars.
"""

import os
import pandas as pd
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional
from dotenv import load_dotenv

# Import cTrader SDK components
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor

load_dotenv()

class LiveCTraderFeed:
    def __init__(self, symbol_name: str = "EURUSD"):
        self.client_id = os.getenv("CTRADER_CLIENT_ID")
        self.client_secret = os.getenv("CTRADER_CLIENT_SECRET")
        self.access_token = os.getenv("CTRADER_ACCESS_TOKEN")
        self.account_id = int(os.getenv("CTRADER_ACCOUNT_ID", "0"))
        self.env = os.getenv("CTRADER_ENV", "demo").lower()
        self.symbol_name = symbol_name
        
        self.symbol_id: Optional[int] = None
        
        # Determine host based on env
        if self.env == "demo":
            host = EndPoints.PROTOBUF_DEMO_HOST
        else:
            host = EndPoints.PROTOBUF_LIVE_HOST
            
        self.client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        self.client.setConnectedCallback(self._on_connected)
        self.client.setDisconnectedCallback(self._on_disconnected)
        self.client.setMessageReceivedCallback(self._on_message)

    def _on_connected(self, client):
        print(f"[+] Connected to cTrader ({self.env.upper()}). Authenticating App...")
        req = ProtoOAApplicationAuthReq()
        req.clientId = self.client_id
        req.clientSecret = self.client_secret
        client.send(req)

    def _on_disconnected(self, client, reason):
        print(f"[-] Disconnected: {reason}")

    def _on_message(self, client, message):
        msg_type = message.payloadType
        
        # --- Application Auth Success ---
        if msg_type == ProtoOAApplicationAuthRes().payloadType:
            print("[+] App Authenticated. Authenticating Account...")
            req = ProtoOAAccountAuthReq()
            req.ctidTraderAccountId = self.account_id
            req.accessToken = self.access_token
            client.send(req)
            
        # --- Account Auth Success ---
        elif msg_type == ProtoOAAccountAuthRes().payloadType:
            print("[+] Account Authenticated. Finding Symbol ID...")
            req = ProtoOASymbolsListReq()
            req.ctidTraderAccountId = self.account_id
            client.send(req)
            
        # --- Symbols List Received ---
        elif msg_type == ProtoOASymbolsListRes().payloadType:
            for sym in message.symbol:
                if sym.symbolName == self.symbol_name:
                    self.symbol_id = sym.symbolId
                    print(f"[+] Found {self.symbol_name} (ID: {self.symbol_id})")
                    self._subscribe(client)
                    break
                    
        # --- Live Spot Event (Contains Tick Data & Trendbar Updates) ---
        elif msg_type == ProtoOASpotEvent().payloadType:
            if message.symbolId != self.symbol_id:
                return
                
            # 1. Print the live Bid price (raw is divided by 100000)
            if message.HasField("bid"):
                bid = message.bid / 100000.0
                
            # 2. Check for candle updates
            if message.HasField("trendbar"):
                tb = message.trendbar[0]
                if tb.period == ProtoOATrendbarPeriod.M5:
                    # Decode candle prices using the low + delta method
                    digits = 5
                    divisor = 10 ** digits
                    low = tb.low / divisor
                    high = (tb.low + tb.deltaHigh) / divisor
                    close = (tb.low + tb.deltaClose) / divisor
                    
                    bar_time = datetime.fromtimestamp(tb.utcTimestampInMinutes * 60, tz=timezone.utc)
                    
                    print(f"[M5 UPDATE] {bar_time.strftime('%H:%M')} | "
                          f"H: {high:.5f} | L: {low:.5f} | C: {close:.5f}")

    def _subscribe(self, client):
        # Subscribe to Spots (Required for Trendbars to flow)
        req_spots = ProtoOASubscribeSpotsReq()
        req_spots.ctidTraderAccountId = self.account_id
        req_spots.symbolId.append(self.symbol_id)
        client.send(req_spots)
        print("[+] Subscribed to live Spots.")
        
        # Subscribe to Live M5 Trendbars
        req_bars = ProtoOASubscribeLiveTrendbarReq()
        req_bars.ctidTraderAccountId = self.account_id
        req_bars.symbolId = self.symbol_id
        req_bars.period = ProtoOATrendbarPeriod.M5
        client.send(req_bars)
        print("[+] Subscribed to live M5 Trendbars.")
        print("\n[*] Waiting for live market data...\n" + "-"*40)

    def start(self):
        print(f"[*] Starting Live Feed for {self.symbol_name}...")
        self.client.startService()
        reactor.run() # This blocks and keeps the connection alive