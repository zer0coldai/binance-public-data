from datetime import *

YEARS = [str(y) for y in range(2017, datetime.now().year + 1)]
INTERVALS = ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1mo"]
DAILY_INTERVALS = ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]
TRADING_TYPE = ["spot", "um", "cm"]
MONTHS = list(range(1,13))
PERIOD_START_DATE = '2020-01-01'
BASE_URL = 'https://data.binance.vision/'
START_DATE = date(int(YEARS[0]), MONTHS[0], 1)
END_DATE = datetime.date(datetime.now())

# Default start dates per trading type (earliest monthly archive available on Binance)
TRADING_TYPE_START_DATE = {
  'spot': '2017-01-01',
  'um':   '2020-01-01',
  'cm':   '2020-01-01',
}
