from django.conf.urls import url
from .views import (
    StockListView, StockDetailView, InsiderTradeListView, StockDeltaView,
    StockAnalyticsView
)

urlpatterns = [
    url(r'^$', StockListView.as_view(), name='stock-list'),
    url(r'^(?P<slug>[\w.-]+)/$', StockDetailView.as_view(), name='stock-detail'),
    url(r'^(?P<slug>[\w.-]+)/insider/$', InsiderTradeListView.as_view(), name='insiders-trades'),
    url(r'^(?P<slug>[\w.-]+)/insider/(?P<insider_id>\d+)/$', InsiderTradeListView.as_view(), name='insider-trade'),
    url(r'^(?P<slug>[\w.-]+)/delta/$', StockDeltaView.as_view(), name='delta-list'),
    url(r'^(?P<slug>[\w.-]+)/analytics/$', StockAnalyticsView.as_view(), name='analytics')
]
