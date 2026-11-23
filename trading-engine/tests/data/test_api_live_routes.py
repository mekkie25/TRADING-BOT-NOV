import unittest

from fastapi import HTTPException

import api

EXPECTED_INSTRUMENTS = sorted(
    ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD", "DAX", "US30", "NAS100"]
)
FIELDS_THE_SCREEN_READS = (
    "connectionState",
    "environment",
    "symbol",
    "message",
    "quote",
    "lastClosedCandle",
)


class LiveRoutesForTheScreenTests(unittest.TestCase):
    def test_pairs_list_has_all_eight_instruments(self):
        pairs = api.get_pairs()

        self.assertEqual(sorted(pair["symbol"] for pair in pairs), EXPECTED_INSTRUMENTS)
        for pair in pairs:
            self.assertTrue(pair["displayName"])

    def test_live_all_has_every_instrument_with_the_fields_the_screen_reads(self):
        snapshots = api.get_live_market_data_all()

        self.assertEqual(sorted(snapshots), EXPECTED_INSTRUMENTS)
        for symbol, snapshot in snapshots.items():
            for field in FIELDS_THE_SCREEN_READS:
                self.assertIn(field, snapshot, f"{symbol} is missing {field}")
            self.assertEqual(snapshot["symbol"], symbol)

    def test_one_instrument_can_be_asked_for_by_name_in_any_letter_case(self):
        snapshot = api.get_live_market_data("btcusd")

        self.assertEqual(snapshot["symbol"], "BTCUSD")

    def test_unknown_instrument_gives_a_clear_404_for_live_and_snapshot(self):
        with self.assertRaises(HTTPException) as live_error:
            api.get_live_market_data("DOGEUSD")
        with self.assertRaises(HTTPException) as snapshot_error:
            api.get_market_snapshot("DOGEUSD")

        self.assertEqual(live_error.exception.status_code, 404)
        self.assertEqual(snapshot_error.exception.status_code, 404)
        self.assertIn("Unknown instrument", live_error.exception.detail)

    def test_known_instrument_without_a_report_yet_gives_503_not_a_crash(self):
        with self.assertRaises(HTTPException) as caught:
            api.get_market_snapshot("DAX")

        self.assertEqual(caught.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()