from django.core.management import BaseCommand
from finance.base.importer import Importer


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('--path')
        parser.add_argument('--thread_number', type=int)

    def handle(self, *args, **options):
        kwargs = {
            'tickers': Importer.get_tickers(options['path'])
        }
        if options['thread_number']:
            kwargs['thread_number'] = options['thread_number']
        importer = Importer(**kwargs)
        stock_prices_parser = importer.import_stock_prices()
        insider_trades_parser = importer.import_insider_trades()

        stock_prices_parser.join_all()
        insider_trades_parser.join_all()

        self.stdout.write(self.style.SUCCESS('Import finished'))
