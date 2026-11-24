"""The list of strategies the backtester can run, and the shared adapter that runs them.

Most strategy files expose a plain `evaluate(...)` function. The simulator needs an
object with `name`, `timeframe`, `symbols` and `on_bar(ctx)`. `EvaluateStrategy` is
that object for ANY evaluate-style strategy, so no strategy file has to change.

The adapter does not alter any strategy's logic: it builds the market facts exactly
the way the existing strategy classes do (Grabber, Asia fade, ...) and hands the
candles, facts, instrument spec, parameters, variant and timeframe to `evaluate`.
"""

import importlib
import inspect
from typing import Callable, Dict, List, Optional

from broker.instrument_specs import get_instrument_spec
from engine.models import Signal
from strategies.base import BarContext
from strategies.context import build_market_facts

# strategy id -> module that holds its evaluate() function
STRATEGY_MODULES: Dict[str, str] = {
    "all_time_high": "strategies.all_time_high",
    "asia_breakout": "strategies.asia_breakout",
    "asia_fade": "strategies.asia_fade",
    "cracker": "strategies.cracker",
    "ema_200_pullback": "strategies.ema_200_pullback",
    "first_pullback": "strategies.first_pullback",
    "grabber": "strategies.grabber",
    "grids": "strategies.grids",
    "ifvg": "strategies.ifvg",
    "intra_range": "strategies.intra_range",
    "oes": "strategies.oes",
    "orb": "strategies.orb",
    "orb_value_reversal": "strategies.orb_value_reversal",
    "pdh_pdl_reversal": "strategies.pdh_pdl_reversal",
    "power_ranger": "strategies.power_ranger",
    "reversal": "strategies.reversal",
    "session_low_reversal": "strategies.session_low_reversal",
    "value_area": "strategies.value_area",
    "vwap": "strategies.vwap",
}

DEFAULT_TIMEFRAME = "M5"


def _module(strategy_id: str):
    if strategy_id not in STRATEGY_MODULES:
        raise KeyError(f"Unknown strategy: {strategy_id}")
    return importlib.import_module(STRATEGY_MODULES[strategy_id])


def _evaluate_function(strategy_id: str) -> Callable[..., Optional[Signal]]:
    return _module(strategy_id).evaluate


def variants_for(strategy_id: str) -> List[str]:
    """The variant names the strategy accepts (empty when it has no variants)."""
    declared = getattr(_module(strategy_id), "VARIANTS", None)
    return list(declared) if declared else []


def default_variant_for(strategy_id: str) -> Optional[str]:
    """The variant the strategy uses when none is chosen (its evaluate() default)."""
    parameter = inspect.signature(_evaluate_function(strategy_id)).parameters.get("variant")
    if parameter is None or parameter.default is inspect.Parameter.empty:
        return None
    return parameter.default


class EvaluateStrategy:
    """Runs one evaluate()-style strategy inside the simulator."""

    def __init__(
        self,
        strategy_id: str,
        timeframe: str = DEFAULT_TIMEFRAME,
        variant: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self._evaluate = _evaluate_function(strategy_id)
        self._accepted = set(inspect.signature(self._evaluate).parameters)

        allowed_variants = variants_for(strategy_id)
        if variant is not None and allowed_variants and variant not in allowed_variants:
            raise ValueError(
                f"Unknown variant '{variant}' for {strategy_id}. "
                f"Choose one of: {', '.join(allowed_variants)}."
            )

        self.name = strategy_id
        self.timeframe = timeframe.upper()
        self.symbols = symbols or ["EURUSD"]
        self.variant = variant or default_variant_for(strategy_id)
        self.parameters = parameters or {}

    def on_bar(self, ctx: BarContext) -> Optional[Signal]:
        spec = get_instrument_spec(ctx.symbol)
        facts = build_market_facts(ctx.df, self.timeframe, ctx.current_time, spec)

        arguments = {
            "candles": ctx.df,
            "facts": facts,
            "instrument_spec": spec,
            "parameters": self.parameters,
        }
        if "variant" in self._accepted and self.variant is not None:
            arguments["variant"] = self.variant
        if "timeframe" in self._accepted:
            arguments["timeframe"] = self.timeframe
        return self._evaluate(**arguments)


def build_strategy(
    strategy_id: str,
    timeframe: str = DEFAULT_TIMEFRAME,
    variant: Optional[str] = None,
    symbol: str = "EURUSD",
) -> EvaluateStrategy:
    return EvaluateStrategy(
        strategy_id,
        timeframe=timeframe,
        variant=variant,
        symbols=[symbol.upper()],
    )


def list_strategy_ids() -> List[str]:
    return list(STRATEGY_MODULES)
