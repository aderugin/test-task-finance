import requests
import logging

from decimal import Decimal, InvalidOperation
from threading import Thread
from datetime import datetime, date
from lxml.html import fromstring
from .utils import split_list

from django.utils.lru_cache import lru_cache

logger = logging.getLogger(__name__)


class ParserError(Exception):
    pass


class ThreadedParser(object):
    """
    @type :parser: stock_prices_parser | insider_trades_parser
    @type :stocks: list
    @type :thread_number: int
    @type :callback: None | callable
    """
    result = None
    threads = None

    def __init__(self, parser, stocks, thread_number=1, callback=None):
        assert (parser is stock_prices_parser) or (parser is insider_trades_parser)
        assert isinstance(stocks, list)
        assert isinstance(thread_number, int)
        assert callable(callback) or callback is None

        self.result = []
        self.threads = [
            Thread(target=parser, args=(slugs, self.result, callback))
            for slugs in split_list(stocks, thread_number)
        ]

    def start_all(self):
        for thread in self.threads:
            thread.start()

    def join_all(self):
        for thread in self.threads:
            thread.join()


def stock_prices_parser(stock_slugs, result, callback=None):
    for stock_slug in stock_slugs:
        print('Prices', stock_slug)
        prices = NasdaqPricesParser(stock_slug).get_stock_prices()
        if callable(callback):
            callback(prices)
        else:
            result.append(prices)


def insider_trades_parser(stock_slugs, result, callback=None):
    for stock_slug in stock_slugs:
        print('Insiders', stock_slug)
        trades = NasdaqInsiderTradesParser(stock_slug).get_insider_trades()
        if callable(callback):
            callback(trades)
        else:
            result.append(trades)


def parse_tickers_file(path):
    with open(path, 'r') as f:
        return [line.strip().lower() for line in f.readlines()]


class NasdaqPricesParser(object):
    url = None
    stock_slug = None

    def __init__(self, stock_slug):
        self.stock_slug = stock_slug
        self.url = 'http://www.nasdaq.com/symbol/%s/historical' % stock_slug

    def get_stock_prices(self):
        rows = []
        for row in self._get_raw_rows():
            if len(row) != 6:
                continue
            rows.append({
                'date': _normalize_date(_normalize_value(row[0])),
                'open': _normalize_decimal(_normalize_value(row[1])),
                'high': _normalize_decimal(_normalize_value(row[2])),
                'low': _normalize_decimal(_normalize_value(row[3])),
                'close': _normalize_decimal(_normalize_value(row[4])),
                'volume': _normalize_integer(_normalize_value(row[5])),
                'stock': self.stock_slug
            })
        return rows

    def _get_raw_rows(self):
        items = fromstring(self._get_html_string()).xpath(
            '//*[@id="quotes_content_left_pnlAJAX"]/table/tbody/tr'
        )
        return items

    def _get_html_string(self):
        response = requests.get(self.url)
        if response.status_code != 200:
            logger.debug('Parser GET error, %s' % url)
            raise ParserError('Parser GET error, %s' % self.url)
        return response.text


class NasdaqInsiderTradesParser(object):
    MAX_PAGES = 10
    stock_slug = None
    url = None

    def __init__(self, stock_slug):
        self.stock_slug = stock_slug
        self.url = 'http://www.nasdaq.com/symbol/%s/insider-trades' % stock_slug

    def get_insider_trades(self):
        rows = []
        for url in self._get_pages_urls():
            for row in self._get_raw_rows(url):
                if len(row) != 8:
                    continue
                rows.append({
                    'insider': _normalize_value(row[0][0]),
                    'relation': _normalize_value(row[1]),
                    'date': _normalize_date(_normalize_value(row[2])),
                    'transaction_type': _normalize_value(row[3]),
                    'owner_type': _normalize_value(row[4]),
                    'shares_traded': _normalize_integer(_normalize_value(row[5])),
                    'last_price': _normalize_decimal(_normalize_value(row[6])),
                    'shares_held': _normalize_integer(_normalize_value(row[7])),
                    'stock': self.stock_slug
                })
        return rows

    def _get_pages_urls(self):
        raw_urls = fromstring(self._get_html_string(self.url)).xpath(
            '//ul[@class="pager"]//a[@class="pagerlink"]'
        )
        urls = list(set((ru.attrib['href'] for ru in raw_urls)))[:self.MAX_PAGES - 1]
        urls.append(self.url)
        return urls

    def _get_raw_rows(self, url):
        items = fromstring(self._get_html_string(url)).xpath(
            '//div[@class="genTable"]/table[@class="certain-width"]/tr'
        )
        return items

    @lru_cache()
    def _get_html_string(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.debug('Parser GET error, %s' % url)
            raise ParserError('Parser GET error, %s' % url)
        return response.text


def _normalize_date(value):
    try:
        return datetime.strptime(value, '%m/%d/%Y').date()
    except ValueError:
        return date.today()


def _normalize_decimal(value):
    try:
        if value is not None:
            value = value.replace(',', '')
        return Decimal(value)
    except (InvalidOperation, TypeError):
        pass
    return None


def _normalize_integer(value):
    try:
        return int(value.replace(',', ''))
    except ValueError:
        pass
    return None


def _normalize_value(value):
    try:
        return value.text.strip()
    except AttributeError:
        pass
    return None
