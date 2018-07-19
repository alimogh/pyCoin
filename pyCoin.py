import requests
from tabulate import tabulate
from datetime import datetime


class Crypto(object):
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.symbol = data["symbol"]
        self.website_slug = data["website_slug"]
        self.currencies = None

    def get_ticker(self, convert="USD"):
        base_url = "https://api.coinmarketcap.com/v2/"
        url = f"{base_url}ticker/{self.id}/?convert={convert}"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            # Add the ticker value from the JSON
            ticker = r.json()["data"]
            self.set_ticker(ticker, convert)
        else:
            raise ConnectionError(f"{url} [{r.status_code}]")

    def set_ticker(self, ticker, conv):
        self.rank = ticker["rank"]
        keys = ["price", "volume_24h", "percent_change_24h",
                "percent_change_7d"]
        data = {key: ticker["quotes"][conv][key] for key in keys}

        if self.currencies:
            self.currencies[conv] = data
        else:
            self.currencies = {conv: data}


class bcolors:
    WHITE = '\033[97m'
    CYAN = '\033[36m'
    MAGENTA = '\033[35m'
    BLUE = '\033[94m'
    GREEN = '\033[32m'
    YELLOW = '\033[93m'
    RED = '\033[31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def bold(text):
    return bcolors.BOLD + str(text) + bcolors.ENDC


def color(text, color):
    colors = {"m": bcolors.MAGENTA, "b": bcolors.BLUE, "y": bcolors.YELLOW,
              "w": bcolors.WHITE, "c": bcolors.CYAN, "r": bcolors.RED,
              "g": bcolors.GREEN}
    return colors[color] + str(text) + bcolors.ENDC


def color_percent(value):
    if value < 0:
        return color(value / 100, "r")
    else:
        return color(value / 100, "g")


def load_cmc_ids():
    # Get the JSON file from CMC API
    url = "https://api.coinmarketcap.com/v2/listings/"
    r = requests.get(url, timeout=10)

    if r.status_code == 200:
        # Parse the JSON into a dict of Crypto objects
        return {data["symbol"]: Crypto(data) for data in r.json()["data"]}
    else:
        raise ConnectionError(f"{url} [{r.status_code}]")


def get_top_10(cryptos, convert="USD"):
    selected = set()
    base_url = "https://api.coinmarketcap.com/v2/"
    for conv in convert.split(","):
        url = f"{base_url}ticker/?limit=10&convert={conv}"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            # Parse the JSON and update the Crypto objects
            data = r.json()['data']
            for key in data:
                cryptos[data[key]["symbol"]].set_ticker(data[key], conv)
                selected.add(cryptos[data[key]["symbol"]])
        else:
            raise ConnectionError(f"{url} [{r.status_code}]")

    return list(selected)


def get_symbols(cryptos, symbols, convert="USD"):
    selected = set()
    for symbol in symbols.split(","):
        if symbol in cryptos:
            for conv in convert.split(","):
                cryptos[symbol].get_ticker(conv)
                selected.add(cryptos[symbol])

        else:
            print(color(f"Couldn't find '{symbol}' on CoinMarketCap.com", 'm'))

    return list(selected)


def sort_selection(selection, sort_value, curr):
    cases = {"rank": lambda x: x.rank,
             "price": lambda x: x.currencies[curr]["price"],
             "change_24h": lambda x: x.currencies[curr]["percent_change_24h"],
             "change_7d": lambda x: x.currencies[curr]["percent_change_7d"],
             "volume": lambda x: x.currencies[curr]["volume_24h"]}

    return sorted(selection, key=cases[sort_value.replace("-", "")],
                  reverse="-" not in sort_value)


def print_selection_onetab(selection, sort_value):
    # Generate a list of lists containing the data to print
    to_print = []

    # Sort the selection
    selection = sort_selection(selection, sort_value,
                               selection[0].currencies[0])

    for item in selection:
        currs = item.currencies
        prices = [currs[c]['price'] for c in currs]
        volumes = [currs[c]['volume_24h'] for c in currs]
        percent_24h = [color_percent(currs[c]['percent_change_24h'])
                       for c in currs]
        percent_7d = [color_percent(currs[c]['percent_change_7d'])
                      for c in currs]

        data = [bold(item.rank), item.symbol, item.name]
        data += prices + percent_24h + percent_7d + volumes
        to_print.append(data)

    currs = selection[0].currencies
    headers = ["Rank", "Symbol", "Name"] + [f"Price ({c})" for c in currs] + \
              [f"24h-Change ({c})" for c in currs] + \
              [f"7d-Change ({c})" for c in currs] + \
              [f"24h-Volume ({c})" for c in currs]
    headers = [bold(h) for h in headers]

    floatfmt = [""] * 3 + [".8f" if c == 'BTC' else ".4f" for c in currs] + \
               [".2%" for _ in range(len(currs) * 2)] + \
               [".4f" if c == 'BTC' else ",.0f" for c in currs]

    print(tabulate(to_print, headers=headers, floatfmt=floatfmt))
    # Print the source and timestamp
    print(f"\nSource: {color('https://www.coinmarketcap.com', 'b')} - "
          f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def print_selection_multitab(selection, sort_value):
    for currency in selection[0].currencies:
        # Generate a list of lists containing the data to print
        to_print = []

        # Sort the selection
        selection = sort_selection(selection, sort_value, currency)

        for item in selection:
            currs = item.currencies
            price = currs[currency]['price']
            volume = currs[currency]['volume_24h']
            percent_24h = color_percent(currs[currency]['percent_change_24h'])
            percent_7d = color_percent(currs[currency]['percent_change_7d'])
            data = [bold(item.rank), item.symbol, item.name,
                    price, percent_24h, percent_7d, volume]
            to_print.append(data)

        headers = ["Rank", "Symbol", "Name", f"Price ({currency})",
                   f"24h-Change ({currency})", f"7d-Change ({currency})",
                   f"24h-Volume ({currency})"]
        headers = [bold(h) for h in headers]

        floatfmt = ["", "", "", f"{'.8f' if currency == 'BTC' else '.4f'}",
                    ".2%", ".2%", f"{'.4f' if currency == 'BTC' else ',.0f'}"]

        print(color(bold("\n> " + currency), "y"))
        print(tabulate(to_print, headers=headers, floatfmt=floatfmt))
    # Print the source and timestamp
    print(f"\nSource: {color('https://www.coinmarketcap.com', 'w')} - "
          f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main(currency, symbols, sort_value):
    # Load the crypto ids from CMC
    cryptos = load_cmc_ids()

    # Get the tickers of the top 10 cryptos
    if symbols:
        selection = get_symbols(cryptos, symbols, currency)
    else:
        selection = get_top_10(cryptos, currency)

    # Print the selection if any
    if selection:
        # print_selection_onetab(selection, sort_value)
        print_selection_multitab(selection, sort_value)


if __name__ == '__main__':
    import argparse

    supported_currencies = ["AUD", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK",
                            "DKK", "EUR", "GBP", "HKD", "HUF", "IDR", "ILS",
                            "INR", "JPY", "KRW", "MXN", "MYR", "NOK", "NZD",
                            "PHP", "PKR", "PLN", "RUB", "SEK", "SGD", "THB",
                            "TRY", "TWD", "ZAR", "BTC", "ETH", "XRP", "LTC",
                            "BCH"]
    sorts = ["rank", "rank-", "price", "price-", "change_24h", "change_24h-",
             "change_7d", "change_7d-", "volume", "volume-"]

    parser = argparse.ArgumentParser(description='Displays cryptocurrencies '
                                     'data from CMC in the terminal')
    parser.add_argument('--curr', default='USD', type=str,
                        help=f'Currency used for the price and volume '
                        '(for more than one, separate them with a comma : '
                        'USD,BTC). Valid currencies: '
                        '{bold(", ".join(supported_currencies))}')
    parser.add_argument('--crypto', default=None, type=str,
                        help='Symbols of the cryptocurrencies to display '
                        '(default top10).')
    parser.add_argument('--sort', default='rank-', type=str, choices=sorts,
                        help='Cryptocurrencies sorting in the table.')

    args = parser.parse_args()

    args.curr = args.curr.upper()
    args.sort = args.sort.lower()

    # Check if the currency is supported by CMC, if not use 'USD'
    for curr in args.curr.split(","):
        if curr not in supported_currencies + ["USD"]:
            print(color(f"'{args.curr}' is not a valid currency value, "
                        "using 'USD'", 'm'))
            args.curr = "USD"
            break

    if args.crypto:
        main(args.curr, args.crypto.upper().replace(" ", ""), args.sort)
    else:
        main(args.curr, None, args.sort)
