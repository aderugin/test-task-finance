from django.db import models, IntegrityError


class Stock(models.Model):
    slug = models.SlugField(unique=True)

    @models.permalink
    def get_absolute_url(self):
        return ('stock-detail', (self.slug,))


STOCK_PRICE_TYPES = ('open', 'high', 'low', 'close')


class StockPriceQuerySet(models.QuerySet):
    def delta(self, stock, max_delta, type_):
        assert isinstance(stock, Stock)
        assert isinstance(max_delta, int)
        assert type_ in STOCK_PRICE_TYPES

        stock_prices = self.filter(
            stock=stock, **{'%s__isnull' % type_: False}
        ).values('date', type_).order_by('date')
        last_value = 0
        last_date = None
        first_loop = True
        delta = 0
        result = []
        for stock_price in stock_prices:
            if first_loop:
                last_value = stock_price[type_]
                last_date = stock_price['date']
                first_loop = False
                continue
            delta += stock_price[type_] - last_value
            if abs(delta) > max_delta:
                result.append({
                    'date_from': last_date,
                    'date_to': stock_price['date'],
                    'delta': delta
                })
                delta = 0
                last_date = stock_price['date']
            last_value = stock_price[type_]
        return result

    def in_period(self, date_from, date_to):
        return self.filter(date__gte=date_from, date__lte=date_to)

    def with_previous(self):
        queryset = self.order_by('date')
        last_stock_price = None
        for stock_price in queryset:
            if last_stock_price is None:
                last_stock_price = stock_price
                continue
            stock_price._previous_row = last_stock_price
            last_stock_price = stock_price
        return queryset


class StockPrice(models.Model):
    date = models.DateField()
    open = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    high = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    low = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    close = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    volume = models.PositiveIntegerField(null=True)
    stock = models.ForeignKey(Stock, related_name='prices', on_delete=models.CASCADE)

    objects = StockPriceQuerySet.as_manager()

    class Meta:
        unique_together = ('date', 'stock')
        ordering = ['-date']

    @property
    def open_delta(self):
        return self._get_delta('open')

    @property
    def high_delta(self):
        return self._get_delta('high')

    @property
    def low_delta(self):
        return self._get_delta('low')

    @property
    def close_delta(self):
        return self._get_delta('close')

    def _get_delta(self, field_name):
        if hasattr(self, '_previous_row'):
            return getattr(self, field_name) - getattr(self._previous_row, field_name)
        return None


class InsiderManager(models.Manager):
    def safety_get_or_create(self, **kwargs):
        try:
            instance = self.create(**kwargs)
        except IntegrityError:
            instance = self.get(**kwargs)
        return instance


class Insider(models.Model):
    name = models.CharField(max_length=255)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    objects = InsiderManager()

    class Meta:
        unique_together = ('name', 'stock')

    def __str__(self):
        return self.name


class InsiderTrade(models.Model):
    date = models.DateField()
    insider = models.ForeignKey(Insider, related_name='trades', on_delete=models.CASCADE)
    relation = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=255)
    owner_type = models.CharField(max_length=255)
    shares_traded = models.PositiveIntegerField(null=True)
    last_price = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    shares_held = models.PositiveIntegerField(null=True)

    class Meta:
        unique_together = (
            'insider', 'date', 'transaction_type', 'shares_traded', 'last_price',
            'shares_held'
        )
        ordering = ['-date']
