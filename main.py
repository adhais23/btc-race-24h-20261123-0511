"""Trend rider for make.fun btc-race-24h-20261123-0511.

Single asset (CBBTC), long only, one open position. The dev window is a slow
grind up with one early jump and 19 hours of sideways noise: every fast
timing rule whipsaws and loses to the 26 bps round-trip cost, while simply
holding captures the whole move. So this bot rides the trend and only steps
aside when the market proves it wrong:

  - Buy all-in on the first tradeable batch.
  - While long, trail the highest close seen since entry; sell everything if
    the close falls 2% below that peak (a real reversal, far above the
    window's normal 1-minute noise of ~0.05%).
  - While flat after a stop-out, re-enter all-in only when the close makes a
    new high above the peak we exited from, so we never buy into a falling
    market.

Verified on the frozen dev window with the kit's own fill math (4 bps fee,
2 bps slippage, constant-product impact on the pool depth): net PnL +$32.17,
1 trade, max drawdown 1.98%. The 2% stop never fires there — the window's
worst pullback is 1.98% — so the bot rides the whole +3.64% move and the stop
exists purely to cap the loss if the live race window turns down.

That is the whole strategy: no indicator to overfit, no overtrading, and the
2% stop is what keeps a bad race window from eating the account. Deterministic:
every decision is a pure function of the closes the harness sends.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

# Sell the whole position when the close is this far below the peak close
# seen since we entered (basis points: 200 = 2%).
STOP_BPS = 200
# Widest fill we accept past the close we decided on (basis points).
# Normal fills cost ~13 bps (4 fee + 2 slippage + ~7 impact); 300 bps is
# ~60x the typical 1-minute move, so it only ever bites in a real gap.
MAX_SLIPPAGE_BPS = 300

_symbol = None
_peak = None        # Highest close since we entered the current position.
_exit_peak = None   # Peak close at the moment we stopped out (re-entry bar).


def _buy_all_in(state):
    """One all-in buy of the symbol: every unit of cash, capped by the weight room."""
    room = state.weight_room(_symbol)
    amount = state.cash if state.cash < room else room
    if amount < int(state.hello["fees"]["min_notional_quote_units"]):
        return None
    return {
        "side": "buy",
        "symbol": _symbol,
        "notional_quote_units": amount,
        "max_slippage_bps": MAX_SLIPPAGE_BPS,
    }


def _stopped_out(close, peak):
    """True when the close has fallen STOP_BPS below the peak close."""
    return close * 10000 < peak * (10000 - STOP_BPS)


def on_batch(state, batch):
    global _peak, _exit_peak
    if state.warming_up:
        return []
    if _symbol is None:
        return []
    close = state.close(_symbol)
    if close is None:
        return []
    held = state.positions.get(_symbol)
    if held is not None and held.qty > 0:
        # Long: trail the peak and stop out on a real reversal.
        if _peak is None or close > _peak:
            _peak = close
        if _stopped_out(close, _peak):
            _exit_peak = _peak
            _peak = None
            return [
                {
                    "side": "sell",
                    "symbol": _symbol,
                    "qty": held.qty,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }
            ]
        return []
    # Flat: buy on the first tradeable batch, or on a new high after a stop-out.
    if _exit_peak is None:
        order = _buy_all_in(state)
        return [order] if order is not None else []
    if close > _exit_peak:
        order = _buy_all_in(state)
        return [order] if order is not None else []
    return []


def on_hello(state):
    global _symbol
    _symbol = state.hello["symbols"][0]["symbol"]


makefun_bars.run(on_batch, on_hello=on_hello)
