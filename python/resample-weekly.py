#!/usr/bin/env python

"""
  Derive weekly (1w) klines from downloaded daily (1d) archives.

  Binance stopped publishing the 1w monthly archive for USDT-M futures
  after 2024-01 (with an earlier gap in mid-2023 for some symbols), so a
  native 1w series is incomplete. This rebuilds a full weekly series from
  the 1d data instead, using the same Monday-Sunday UTC week boundaries
  Binance's own 1w files use.

  e.g. STORE_DIRECTORY=/data ./resample-weekly.py -t um -s BTCUSDT ETHUSDT
"""

import glob
import os
import sys
from argparse import ArgumentParser

import pandas as pd

from utility import get_destination_dir, get_path

KLINE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "count",
    "taker_buy_volume", "taker_buy_quote_volume", "ignore",
]
SUMMED_COLUMNS = ["volume", "quote_volume", "taker_buy_volume", "taker_buy_quote_volume"]
DAY_MS = 24 * 60 * 60 * 1000
WEEK_MS = 7 * DAY_MS


def read_kline_csv(path):
  # Binance added a header row to archives partway through 2021; older files have none.
  with open(path) as fh:
    has_header = fh.readline().startswith("open_time")
  return pd.read_csv(path, header=0 if has_header else None,
                      names=None if has_header else KLINE_COLUMNS)


def load_daily_klines(trading_type, symbol):
  """Concatenate every downloaded 1d csv (monthly + current-month daily) for a symbol."""
  frames = []
  for time_period in ("monthly", "daily"):
    csv_dir = get_destination_dir(get_path(trading_type, "klines", time_period, symbol, "1d"))
    for csv_path in sorted(glob.glob(os.path.join(csv_dir, "*.csv"))):
      frames.append(read_kline_csv(csv_path))
  if not frames:
    return None
  daily = pd.concat(frames, ignore_index=True)
  return daily.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def resample_to_weekly(daily):
  """Aggregate daily bars into Monday-Sunday UTC weeks; drop weeks with missing days."""
  dt = pd.to_datetime(daily["open_time"], unit="ms", utc=True)
  week_start = (dt - pd.to_timedelta(dt.dt.weekday, unit="D")).dt.normalize()

  weekly = daily.groupby(week_start).agg(
      open=("open", "first"),
      high=("high", "max"),
      low=("low", "min"),
      close=("close", "last"),
      count=("count", "sum"),
      days=("open_time", "size"),
      **{col: (col, "sum") for col in SUMMED_COLUMNS},
  )
  weekly = weekly[weekly["days"] == 7].drop(columns="days")
  weekly[SUMMED_COLUMNS] = weekly[SUMMED_COLUMNS].round(8)

  weekly["open_time"] = weekly.index.view("int64") // 1_000_000
  weekly["close_time"] = weekly["open_time"] + WEEK_MS - 1
  weekly["ignore"] = 0
  return weekly.reset_index(drop=True)[KLINE_COLUMNS]


def write_weekly(trading_type, symbol, weekly):
  out_dir = get_destination_dir(get_path(trading_type, "klines", "derived", symbol, "1w"))
  os.makedirs(out_dir, exist_ok=True)
  out_path = os.path.join(out_dir, "{}-1w.csv".format(symbol.upper()))
  weekly.to_csv(out_path, index=False)
  return out_path


def parse_args():
  parser = ArgumentParser(description=__doc__.strip())
  parser.add_argument("-t", dest="type", required=True, choices=["spot", "um", "cm"],
                       help="Trading type of the downloaded 1d archives to resample")
  parser.add_argument("-s", dest="symbols", nargs="+", required=True,
                       help="Single symbol or multiple symbols separated by space")
  return parser.parse_args()


def main():
  args = parse_args()
  for symbol in args.symbols:
    daily = load_daily_klines(args.type, symbol)
    if daily is None:
      print("{}: no 1d klines found, skipping".format(symbol))
      continue
    weekly = resample_to_weekly(daily)
    out_path = write_weekly(args.type, symbol, weekly)
    print("{}: {} weekly bars -> {}".format(symbol, len(weekly), out_path))


if __name__ == "__main__":
  main()
