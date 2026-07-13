#!/usr/bin/env python

"""
  Merge the monthly fundingRate zip archives into a single csv per symbol.

  The script reads downloaded archives from:
    data/futures/<market_type>/monthly/fundingRate/<SYMBOL>/

  and writes consolidated csvs to:
    data/consolidated/fundingRate/<market_type>/<SYMBOL>/<SYMBOL>-fundingRate.csv

  e.g. STORE_DIRECTORY=/data python3 consolidate-futures-fundingRate.py -t um -s BTCDOMUSDT
"""

import glob
import os
import zipfile
from argparse import ArgumentParser

import pandas as pd

from utility import get_destination_dir, get_path

FUNDING_RATE_COLUMNS = [
    "calc_time",
    "funding_interval_hours",
    "last_funding_rate",
]


def source_dir(trading_type, symbol):
  return get_destination_dir(get_path(trading_type, "fundingRate", "monthly", symbol))


def output_dir(trading_type, symbol):
  out_dir = get_destination_dir("data/consolidated/fundingRate/{}/{}".format(trading_type, symbol.upper()))
  os.makedirs(out_dir, exist_ok=True)
  return out_dir


def read_funding_rate_zip(zip_path):
  with zipfile.ZipFile(zip_path) as archive:
    csv_members = [name for name in archive.namelist() if name.endswith(".csv")]
    if not csv_members:
      return None

    csv_member = csv_members[0]
    with archive.open(csv_member) as fh:
      has_header = fh.readline().decode("utf-8").startswith("calc_time")

    with archive.open(csv_member) as fh:
      if has_header:
        return pd.read_csv(fh)
      return pd.read_csv(fh, header=None, names=FUNDING_RATE_COLUMNS)


def merge_symbol(trading_type, symbol):
  frames = []
  src_dir = source_dir(trading_type, symbol)
  for zip_path in sorted(glob.glob(os.path.join(src_dir, "*.zip"))):
    frame = read_funding_rate_zip(zip_path)
    if frame is not None:
      frames.append(frame)
  if not frames:
    return None
  merged = pd.concat(frames, ignore_index=True)
  return merged.drop_duplicates("calc_time").sort_values("calc_time").reset_index(drop=True)


def write_symbol(trading_type, symbol, df):
  out_dir = output_dir(trading_type, symbol)
  out_path = os.path.join(out_dir, "{}-fundingRate.csv".format(symbol.upper()))
  df.to_csv(out_path, index=False)
  return out_path


def consolidate_symbol(trading_type, symbol):
  merged = merge_symbol(trading_type, symbol)
  if merged is None:
    return None
  return write_symbol(trading_type, symbol, merged), len(merged)


def parse_args():
  parser = ArgumentParser(description=__doc__.strip())
  parser.add_argument(
      "-t",
      dest="type",
      required=True,
      choices=["um", "cm"],
      help="Trading type of the downloaded funding rate archives to consolidate",
  )
  parser.add_argument(
      "-s",
      dest="symbols",
      nargs="+",
      help="Single symbol or multiple symbols separated by space\n"
           "defaults to every symbol found on disk",
  )
  return parser.parse_args()


def main():
  args = parse_args()
  symbols = args.symbols
  if not symbols:
    root = get_destination_dir("data/futures/{}/monthly/fundingRate".format(args.type))
    if os.path.isdir(root):
      symbols = sorted(
          name for name in os.listdir(root)
          if os.path.isdir(os.path.join(root, name))
      )
    else:
      symbols = []

  for symbol in symbols:
    result = consolidate_symbol(args.type, symbol)
    if result is None:
      print("{}: no funding rate archives found, skipping".format(symbol))
      continue
    out_path, rows = result
    print("{}: {} rows -> {}".format(symbol, rows, out_path))


if __name__ == "__main__":
  main()
