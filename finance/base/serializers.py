from rest_framework import serializers
from .models import Stock, StockPrice, InsiderTrade, Insider


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ('id', 'slug')


class StockPriceSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)

    class Meta:
        model = StockPrice
        fields = ('date', 'open', 'high', 'low', 'close', 'volume', 'stock')


class StockPriceWithDeltaSerializer(StockPriceSerializer):
    class Meta(StockPriceSerializer.Meta):
        fields = StockPriceSerializer.Meta.fields + (
            'open_delta', 'high_delta', 'low_delta', 'close_delta'
        )


class InsiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insider
        fields = ('id', 'name')


class InsiderTradeSerializer(serializers.ModelSerializer):
    insider = InsiderSerializer(read_only=True)

    class Meta:
        model = InsiderTrade
        fields = (
            'date', 'insider', 'relation', 'transaction_type', 'owner_type',
            'shares_traded', 'last_price', 'shares_held'
        )


class StockDeltaSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    delta = serializers.DecimalField(max_digits=10, decimal_places=4)
