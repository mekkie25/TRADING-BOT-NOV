from data.live_feed import LiveCTraderFeed

# Start the feed for EURUSD
feed = LiveCTraderFeed(symbol_name="EURUSD")
feed.start()