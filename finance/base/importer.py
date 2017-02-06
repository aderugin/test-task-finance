from django.db import IntegrityError
from collections import Iterable

from .parser import (
    ThreadedParser, stock_prices_parser, insider_trades_parser, parse_tickers_file
)
from .models import Stock, StockPrice, Insider, InsiderTrade


class Importer(object):
    """
    @type :thread_number: int
    @type :tickers: Iterable | None
    @type :import_stock_prices: () => ThreadedParser instance
    @type :import_insider_trades: () => ThreadedParser instance
    """
    stocks = None

    def __init__(self, thread_number=1, tickers=None):
        assert isinstance(thread_number, int) and thread_number > 0
        assert isinstance(tickers, Iterable) or tickers is None

        self.thread_number = thread_number
        self._prepare_stocks(tickers)

    def import_stock_prices(self):
        def callback(prices):
            self._create_prices(prices)

        parser = ThreadedParser(
            parser=stock_prices_parser,
            stocks=list(self.stocks.keys()),
            thread_number=self.thread_number,
            callback=callback
        )
        parser.start_all()
        return parser

    def import_insider_trades(self):
        def callback(trades):
            self._create_trades(trades)

        parser = ThreadedParser(
            parser=insider_trades_parser,
            stocks=list(self.stocks.keys()),
            thread_number=self.thread_number,
            callback=callback
        )
        parser.start_all()
        return parser

    def _create_prices(self, prices):
        for price in prices:
            price['stock_id'] = self.stocks[price.pop('stock')]
            try:
                StockPrice.objects.create(**price)
            except IntegrityError:
                pass

    def _create_trades(self, trades):
        for trade in trades:
            insider = Insider.objects.safety_get_or_create(
                name=trade.pop('insider'),
                stock_id=self.stocks[trade.pop('stock')]
            )
            trade['insider'] = insider
            try:
                InsiderTrade.objects.create(**trade)
            except IntegrityError:
                pass

    def _prepare_stocks(self, tickers):
        if tickers is not None:
            exists_slugs = Stock.objects.filter(slug__in=tickers).values_list('slug', flat=True)
            Stock.objects.bulk_create([
                Stock(slug=slug) for slug in set(tickers) - set(exists_slugs)
            ])
        self.stocks = dict(Stock.objects.values_list('slug', 'id'))

    @staticmethod
    def get_tickers(path=None):
        return parse_tickers_file(path or 'tickers.txt')
