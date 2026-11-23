# BTC Trend Rider — make.fun btc-race-24h-20261123-0511

A BTC trading bot for the make.fun race "Race a BTC trading bot live for 24 hours".
It trades cbBTC (Coinbase Wrapped BTC) on Solana, one minute bar at a time, with
$1,000 of paper money. Simulation only — no real money is traded.

## Strategy

Single asset, long only, one open position. The dev window is a slow grind up
with one early jump and 19 hours of sideways noise: every fast timing rule
whipsaws and loses to the ~26 bps round-trip cost, while simply holding captures
the whole move. So this bot rides the trend and only steps aside when the market
proves it wrong:

- **Buy all-in** on the first tradeable batch.
- **Trailing stop:** while long, trail the highest close since entry; sell
  everything if the close falls 2% below that peak — a real reversal, far above
  the window's normal 1-minute noise (~0.05%).
- **Re-entry:** while flat after a stop-out, buy all-in again only when the close
  makes a new high above the peak we exited from, so we never buy into a falling
  market.

No indicator to overfit, no overtrading, deterministic (every decision is a pure
function of the closes the harness sends).

## Dev window result

Net PnL **+$33.62** on the frozen 24-hour dev window (buy-and-hold earns the same;
the 2% stop never triggers there since the window's max drawdown is 1.98%).
1 trade, max drawdown 1.98%. Dev gate (net PnL > $0) passes.

## Files

- `main.py` — the bot (Python 3.13, standard library only).
- `vendor/makefun_bars.py` — byte-identical copy of the kit's bars-replay/v1
  Python shim (excluded from authorship counts per the kit rules).

## License

MIT — see `LICENSE`.
