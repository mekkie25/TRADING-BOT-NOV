from knowledge.fair_value_gap import check_fvg, is_price_in_fvg, is_fvg_invalidated

print("--- TESTING BULLISH FVG ---")
# Fake candles for a Bullish FVG
c1 = {"open": 1.0850, "high": 1.0860, "low": 1.0840, "close": 1.0855}
c2 = {"open": 1.0855, "high": 1.0900, "low": 1.0855, "close": 1.0895} # Massive green push
c3 = {"open": 1.0895, "high": 1.0910, "low": 1.0880, "close": 1.0905} # Low is 1.0880

fvg = check_fvg(c1, c2, c3)
print(f"FVG Found: {fvg['type']}")
print(f"Gap Bottom: {fvg['gap_bottom']}")
print(f"Gap Top: {fvg['gap_top']}")

print("\n--- TESTING ENTRY ---")
current_price = 1.0870 # Price pulls back into the gap
print(f"Price at {current_price}. In gap? {is_price_in_fvg(current_price, fvg)}")

print("\n--- TESTING INVALIDATION ---")
bad_price = 1.0850 # Price crashes below the gap
print(f"Price closes at {bad_price}. Invalidated? {is_fvg_invalidated(bad_price, fvg)}")