#!/usr/bin/env python

"""
  Add the standard kline header row to any downloaded csv that's missing one.

  Binance's own archives only started shipping a header row partway through
  2021; older monthly/daily zips still unpack into headerless csv files. This
  makes every kline csv on disk consistent so it can be read the same way
  (e.g. plain pandas.read_csv) without probing each file first.

  e.g. STORE_DIRECTORY=/data ./normalize-headers.py -t um -s BTCUSDT ETHUSDT
"""

import glob
import os
from argparse import ArgumentParser

from utility import get_destination_dir

KLINE_HEADER = ("open_time,open,high,low,close,volume,close_time,quote_volume,"
                 "count,taker_buy_volume,taker_buy_quote_volume,ignore")


def klines_root(trading_type, time_period):
  trading_type_path = "spot" if trading_type == "spot" else "futures/{}".format(trading_type)
  return get_destination_dir("data/{}/{}/klines/".format(trading_type_path, time_period))


def add_missing_header(csv_path):
  """Prepend the kline header if csv_path doesn't already start with one. Returns True if changed."""
  with open(csv_path) as fh:
    first_line = fh.readline()
    rest = fh.read()
  if first_line.startswith("open_time"):
    return False
  with open(csv_path, "w") as fh:
    fh.write(KLINE_HEADER + "\n" + first_line + rest)
  return True


def normalize(trading_type, symbols):
  fixed = 0
  for time_period in ("monthly", "daily"):
    root = klines_root(trading_type, time_period)
    if not os.path.isdir(root):
      continue
    for symbol in symbols or sorted(os.listdir(root)):
      for csv_path in glob.glob(os.path.join(root, symbol, "*", "*.csv")):
        if add_missing_header(csv_path):
          fixed += 1
  return fixed


def parse_args():
  parser = ArgumentParser(description=__doc__.strip())
  parser.add_argument("-t", dest="type", required=True, choices=["spot", "um", "cm"],
                       help="Trading type of the downloaded archives to normalize")
  parser.add_argument("-s", dest="symbols", nargs="+",
                       help="Single symbol or multiple symbols separated by space\n"
                            "defaults to every symbol found on disk")
  return parser.parse_args()


def main():
  args = parse_args()
  fixed = normalize(args.type, args.symbols)
  print("Added a header to {} csv file(s)".format(fixed))


if __name__ == "__main__":
  main()
