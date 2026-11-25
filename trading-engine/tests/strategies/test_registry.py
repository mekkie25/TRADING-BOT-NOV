"""Tests for the strategy registry and the backtest route that uses it."""

import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

import api
from engine.simulator import BacktestSimulator
from strategies.registry import (
    STRATEGY_MODULES,
    EvaluateStrategy,
    build_strategy,
    default_variant_for,
    list_strategy_ids,
    variants_for,
)


def random_candles(count, minutes, seed=1):
    rng = np.random.default_rng(seed)
    start = datetime(2026, 3, 2, tzinfo=timezone.utc)
    times = [start + timedelta(minutes=minutes * i) for i in range(count)]
    close = 1.10 + np.cumsum(rng.normal(0, 0.0003, count))
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + rng.uniform(0, 0.0003, count)
    low = np.minimum(open_, close) - rng.uniform(0, 0.0003, count)
    return pd.DataFrame(
        {
            "time": times,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.integers(50, 500, count),
        }
    )


class RegistryTests(unittest.TestCase):
    def test_every_listed_strategy_loads_and_looks_like_a_strategy(self):
        self.assertEqual(len(list_strategy_ids()), 19)
        for strategy_id in list_strategy_ids():
            strategy = build_strategy(strategy_id)
            self.assertIsInstance(strategy, EvaluateStrategy)
            self.assertEqual(strategy.name, strategy_id)
            self.assertEqual(strategy.timeframe, "M5")
            self.assertEqual(strategy.symbols, ["EURUSD"])
            self.assertTrue(callable(strategy.on_bar))

    def test_every_strategy_runs_through_the_simulator_with_its_default_variant(self):
        candles = random_candles(120, minutes=5)
        for strategy_id in list_strategy_ids():
            with self.subTest(strategy=strategy_id):
                result = BacktestSimulator(
                    df=candles,
                    strategy=build_strategy(strategy_id, "M5"),
                    starting_balance=10000.0,
                    risk_percent=1.0,
                ).run()
                self.assertGreaterEqual(result.total_trades, 0)

    def test_unknown_strategy_and_unknown_variant_are_refused(self):
        with self.assertRaises(KeyError):
            build_strategy("not_a_strategy")
        with self.assertRaises(ValueError):
            build_strategy("vwap", variant="not_a_variant")

    def test_variants_and_defaults_come_from_the_strategy_files(self):
        self.assertIn("mean_reversion", variants_for("vwap"))
        self.assertIn(default_variant_for("vwap"), variants_for("vwap"))
        self.assertEqual(variants_for("cracker"), [])
        self.assertIsNone(default_variant_for("cracker"))


class BacktestRouteTests(unittest.TestCase):
    def setUp(self):
        # No `with` block: this does not start the live broker feed.
        self.client = TestClient(api.app)

    def request_body(self, **overrides):
        body = {
            "strategyId": "vwap",
            "pairs": ["EURUSD"],
            "timeframe": "D1",
            "historyLength": "1y",
            "startingBalance": 10000,
            "currency": "USD",
            "leverage": 100,
            "riskPerTradePercent": 1,
        }
        body.update(overrides)
        return body

    def test_strategy_list_has_the_test_strategy_and_all_19_real_ones(self):
        ids = [entry["id"] for entry in self.client.get("/api/strategies").json()]

        self.assertEqual(ids[0], "validation_trivial")
        self.assertEqual(set(ids[1:]), set(STRATEGY_MODULES))

    def test_real_strategies_are_not_marked_active_for_live_trading(self):
        entries = self.client.get("/api/strategies").json()

        self.assertTrue(all(not entry["isActive"] for entry in entries if entry["id"] != "validation_trivial"))

    def test_unknown_strategy_gets_a_clear_400(self):
        response = self.client.post("/api/backtests/run", json=self.request_body(strategyId="nope"))

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown strategy", response.json()["detail"])

    def test_unknown_variant_gets_a_clear_400(self):
        response = self.client.post("/api/backtests/run", json=self.request_body(variant="nope"))

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown variant", response.json()["detail"])

    def test_missing_candle_store_gets_a_clear_404(self):
        with patch.object(api.bar_store, "load_m1", return_value=pd.DataFrame()):
            response = self.client.post("/api/backtests/run", json=self.request_body())

        self.assertEqual(response.status_code, 404)
        self.assertIn("candle downloader", response.json()["detail"])

    def test_run_that_would_take_too_long_is_refused_with_a_clear_message(self):
        too_many = random_candles(api.MAX_BACKTEST_CANDLES + 1, minutes=5)
        with patch.object(api.bar_store, "load_m1", return_value=too_many), patch.object(
            api.bar_store, "load_candles", return_value=too_many
        ):
            response = self.client.post(
                "/api/backtests/run",
                json=self.request_body(timeframe="M5", historyLength="Max available"),
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("limit for now", response.json()["detail"])

    def wait_for_job(self, job_id, wanted=("completed", "failed", "cancelled"), seconds=90):
        deadline = time.time() + seconds
        while time.time() < deadline:
            job = self.client.get(f"/api/backtests/jobs/{job_id}").json()
            if job["status"] in wanted:
                return job
            time.sleep(0.2)
        self.fail("The backtest job did not finish in time.")

    def test_registered_strategy_runs_in_the_background_and_reports_its_own_timeframe(self):
        daily = random_candles(400, minutes=24 * 60)
        with patch.object(api.bar_store, "load_m1", return_value=daily), patch.object(
            api.bar_store, "load_candles", return_value=daily
        ):
            response = self.client.post("/api/backtests/run", json=self.request_body())

            self.assertEqual(response.status_code, 200, response.text)
            started = response.json()
            self.assertIn(started["status"], ("running", "completed"))
            self.assertNotIn("_cancel", started)
            job = self.wait_for_job(started["jobId"])

        self.assertEqual(job["status"], "completed", job)
        self.assertEqual(job["progressPercent"], 100)
        result = self.client.get(f"/api/backtests/{job['resultId']}").json()
        self.assertEqual(result["config"]["strategyId"], "vwap")
        self.assertEqual(result["config"]["timeframe"], "D1")
        self.assertEqual(result["prototypeStatus"], "unverified")

    def test_a_crashing_strategy_is_reported_as_failed_with_the_reason(self):
        class Crashing:
            name = "crashing"
            timeframe = "D1"
            symbols = ["EURUSD"]

            def on_bar(self, ctx):
                raise RuntimeError("boom")

        daily = random_candles(400, minutes=24 * 60)
        with patch.object(api.bar_store, "load_m1", return_value=daily), patch.object(
            api.bar_store, "load_candles", return_value=daily
        ), patch.object(api, "build_strategy", return_value=Crashing()):
            started = self.client.post("/api/backtests/run", json=self.request_body()).json()
            job = self.wait_for_job(started["jobId"])

        self.assertEqual(job["status"], "failed")
        self.assertIn("boom", job["currentStep"])

    def test_a_running_backtest_can_be_cancelled(self):
        class Slow:
            name = "slow"
            timeframe = "D1"
            symbols = ["EURUSD"]

            def on_bar(self, ctx):
                time.sleep(0.05)

        daily = random_candles(400, minutes=24 * 60)
        with patch.object(api.bar_store, "load_m1", return_value=daily), patch.object(
            api.bar_store, "load_candles", return_value=daily
        ), patch.object(api, "build_strategy", return_value=Slow()):
            started = self.client.post("/api/backtests/run", json=self.request_body()).json()
            cancelled = self.client.post(f"/api/backtests/jobs/{started['jobId']}/cancel").json()
            time.sleep(0.5)
            job = self.client.get(f"/api/backtests/jobs/{started['jobId']}").json()

        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(job["status"], "cancelled")
        self.assertEqual(job["currentStep"], "Cancelled by user")

    def test_cancelling_an_unknown_job_gets_a_404(self):
        self.assertEqual(self.client.post("/api/backtests/jobs/nope/cancel").status_code, 404)


if __name__ == "__main__":
    unittest.main()
    