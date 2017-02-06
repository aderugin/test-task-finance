from django import forms
from .models import STOCK_PRICE_TYPES


class StockPriceDeltaForm(forms.Form):
    type_ = forms.ChoiceField(
        label='Тип цены', choices=tuple((t, t) for t in STOCK_PRICE_TYPES)
    )
    max_delta = forms.IntegerField(label='Максимальное изменение')


class StockPriceAnalyticsForm(forms.Form):
    date_from = forms.DateField(label='Дата, с')
    date_to = forms.DateField(label='Дата, по')
