#!/usr/bin/env python

"""
  script to download klines.
  set the absolute path destination folder for STORE_DIRECTORY, and run

  e.g. STORE_DIRECTORY=/data/ ./download-kline.py

"""
import os
import sys
from datetime import *
import pandas as pd
from enums import *
from utility import download_file, get_all_symbols, get_parser, get_start_end_date_objects, convert_to_date_object, \
  get_path, get_destination_dir


def _get_save_dir(base_path, date_range=None, folder=None):
  """Compute the save directory matching download_file's path logic."""
  if folder:
    base_path = os.path.join(folder, base_path)
  if date_range:
    base_path = os.path.join(base_path, date_range.replace(" ", "_"))
  return get_destination_dir(base_path, folder)


def download_monthly_klines(trading_type, symbols, num_symbols, intervals, years, months, start_date, end_date, folder, checksum):
  current = 0
  date_range = None

  if start_date and end_date:
    date_range = start_date + " " + end_date

  if not start_date:
    start_date = convert_to_date_object(TRADING_TYPE_START_DATE.get(trading_type, '2017-01-01'))
  else:
    start_date = convert_to_date_object(start_date)

  if not end_date:
    end_date = END_DATE
  else:
    end_date = convert_to_date_object(end_date)

  # Pre-filter years and months to avoid unnecessary iteration
  years = [y for y in years if int(y) >= start_date.year and int(y) <= end_date.year]
  print("Found {} symbols".format(num_symbols))

  for symbol in symbols:
    print("[{}/{}] - start download monthly {} klines ".format(current+1, num_symbols, symbol))
    for interval in intervals:
      # Scan existing files once to skip already downloaded months
      path = get_path(trading_type, "klines", "monthly", symbol, interval)
      save_dir = _get_save_dir(path, date_range, folder)
      existing_files = set(os.listdir(save_dir)) if os.path.isdir(save_dir) else set()
      skipped = 0

      for year in years:
        for month in months:
          current_date = convert_to_date_object('{}-{}-01'.format(year, month))
          if current_date >= start_date and current_date <= end_date:
            file_name = "{}-{}-{}-{}.zip".format(symbol.upper(), interval, year, '{:02d}'.format(month))
            if file_name in existing_files:
              skipped += 1
              continue
            download_file(path, file_name, date_range, folder)

            if checksum == 1:
              checksum_file_name = "{}-{}-{}-{}.zip.CHECKSUM".format(symbol.upper(), interval, year, '{:02d}'.format(month))
              if checksum_file_name not in existing_files:
                download_file(path, checksum_file_name, date_range, folder)

      if skipped > 0:
        print("\n  Skipped {} already downloaded files for {}/{}".format(skipped, symbol, interval))

    current += 1

def download_daily_klines(trading_type, symbols, num_symbols, intervals, dates, start_date, end_date, folder, checksum):
  current = 0
  date_range = None

  if start_date and end_date:
    date_range = start_date + " " + end_date

  if not start_date:
    start_date = convert_to_date_object(TRADING_TYPE_START_DATE.get(trading_type, '2017-01-01'))
  else:
    start_date = convert_to_date_object(start_date)

  if not end_date:
    end_date = END_DATE
  else:
    end_date = convert_to_date_object(end_date)

  #Get valid intervals for daily
  intervals = list(set(intervals) & set(DAILY_INTERVALS))
  # Pre-filter dates to avoid unnecessary iteration
  dates = [d for d in dates if convert_to_date_object(d) >= start_date and convert_to_date_object(d) <= end_date]
  print("Found {} symbols".format(num_symbols))

  for symbol in symbols:
    print("[{}/{}] - start download daily {} klines ".format(current+1, num_symbols, symbol))
    for interval in intervals:
      # Scan existing files once to skip already downloaded dates
      path = get_path(trading_type, "klines", "daily", symbol, interval)
      save_dir = _get_save_dir(path, date_range, folder)
      existing_files = set(os.listdir(save_dir)) if os.path.isdir(save_dir) else set()
      skipped = 0

      for date in dates:
        file_name = "{}-{}-{}.zip".format(symbol.upper(), interval, date)
        if file_name in existing_files:
          skipped += 1
          continue
        download_file(path, file_name, date_range, folder)

        if checksum == 1:
          checksum_file_name = "{}-{}-{}.zip.CHECKSUM".format(symbol.upper(), interval, date)
          if checksum_file_name not in existing_files:
            download_file(path, checksum_file_name, date_range, folder)

      if skipped > 0:
        print("\n  Skipped {} already downloaded files for {}/{}".format(skipped, symbol, interval))

    current += 1

if __name__ == "__main__":
    parser = get_parser('klines')
    args = parser.parse_args(sys.argv[1:])

    if not args.symbols:
      print("fetching all symbols from exchange")
      symbols = get_all_symbols(args.type)
      num_symbols = len(symbols)
    else:
      symbols = args.symbols
      num_symbols = len(symbols)

    if args.dates:
      dates = args.dates
    else:
      period_start = args.startDate if args.startDate else PERIOD_START_DATE
      period = convert_to_date_object(datetime.today().strftime('%Y-%m-%d')) - convert_to_date_object(period_start)
      dates = pd.date_range(end=datetime.today(), periods=period.days + 1).to_pydatetime().tolist()
      dates = [date.strftime("%Y-%m-%d") for date in dates]
      if args.skip_monthly == 0:
        download_monthly_klines(args.type, symbols, num_symbols, args.intervals, args.years, args.months, args.startDate, args.endDate, args.folder, args.checksum)
    if args.skip_daily == 0:
      download_daily_klines(args.type, symbols, num_symbols, args.intervals, dates, args.startDate, args.endDate, args.folder, args.checksum)

