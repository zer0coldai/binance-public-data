#!/usr/bin/env python

"""
  script to download futures fundingRate archives.
  set the absoluate path destination folder for STORE_DIRECTORY, and run

  e.g. STORE_DIRECTORY=/data/ python3 download-futures-fundingRate.py -t um -s BTCDOMUSDT
"""

import sys
from argparse import ArgumentParser, RawTextHelpFormatter

from enums import START_DATE, END_DATE, MONTHS, YEARS
from utility import (
    check_directory,
    convert_to_date_object,
    download_file,
    get_all_symbols,
    get_path,
    match_date_regex,
)


def download_monthly_funding_rate(
    trading_type,
    symbols,
    num_symbols,
    years,
    months,
    start_date,
    end_date,
    folder,
    checksum,
):
    # Binance public archives currently show BTCDOMUSDT starting at 2021-06.
    current = 0
    date_range = None

    if start_date and end_date:
        date_range = start_date + " " + end_date

    if not start_date:
        start_date = START_DATE
    else:
        start_date = convert_to_date_object(start_date)

    if not end_date:
        end_date = END_DATE
    else:
        end_date = convert_to_date_object(end_date)

    print("Found {} symbols".format(num_symbols))

    for symbol in symbols:
        print("[{}/{}] - start download monthly {} fundingRate ".format(current + 1, num_symbols, symbol))
        for year in years:
            for month in months:
                current_date = convert_to_date_object("{}-{}-01".format(year, month))
                if start_date <= current_date <= end_date:
                    path = get_path(trading_type, "fundingRate", "monthly", symbol)
                    file_name = "{}-fundingRate-{}-{:02d}.zip".format(symbol.upper(), year, month)
                    download_file(path, file_name, date_range, folder)

                    if checksum == 1:
                        checksum_path = get_path(trading_type, "fundingRate", "monthly", symbol)
                        checksum_file_name = "{}-fundingRate-{}-{:02d}.zip.CHECKSUM".format(
                            symbol.upper(), year, month
                        )
                        download_file(checksum_path, checksum_file_name, date_range, folder)

        current += 1


def build_parser():
    parser = ArgumentParser(
        description="This is a script to download historical fundingRate data",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "-s",
        dest="symbols",
        nargs="+",
        help="Single symbol or multiple symbols separated by space",
    )
    parser.add_argument(
        "-y",
        dest="years",
        default=YEARS,
        nargs="+",
        choices=YEARS,
        help="Single year or multiple years separated by space",
    )
    parser.add_argument(
        "-m",
        dest="months",
        default=MONTHS,
        nargs="+",
        type=int,
        choices=MONTHS,
        help="Single month or multiple months separated by space",
    )
    parser.add_argument(
        "-startDate",
        dest="startDate",
        type=match_date_regex,
        help="Starting date to download in [YYYY-MM-DD] format",
    )
    parser.add_argument(
        "-endDate",
        dest="endDate",
        type=match_date_regex,
        help="Ending date to download in [YYYY-MM-DD] format",
    )
    parser.add_argument(
        "-folder",
        dest="folder",
        type=check_directory,
        help="Directory to store the downloaded data",
    )
    parser.add_argument(
        "-c",
        dest="checksum",
        default=0,
        type=int,
        choices=[0, 1],
        help="1 to download checksum file, default 0",
    )
    parser.add_argument(
        "-t",
        dest="type",
        required=True,
        choices=["um", "cm"],
        help="Valid trading types: ['um', 'cm']",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:])

    if not args.symbols:
        print("fetching all symbols from exchange")
        symbols = get_all_symbols(args.type)
        num_symbols = len(symbols)
    else:
        symbols = args.symbols
        num_symbols = len(symbols)

    download_monthly_funding_rate(
        args.type,
        symbols,
        num_symbols,
        args.years,
        args.months,
        args.startDate,
        args.endDate,
        args.folder,
        args.checksum,
    )
