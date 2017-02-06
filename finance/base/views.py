from rest_framework.utils.urls import remove_query_param, replace_query_param

from django.http import Http404
from django.http.response import JsonResponse
from django.views.generic import ListView, TemplateView

from .models import Stock, StockPrice, Insider, InsiderTrade
from .serializers import (
    StockSerializer, StockPriceSerializer, InsiderTradeSerializer,
    StockDeltaSerializer, StockPriceWithDeltaSerializer
)
from .forms import StockPriceDeltaForm, StockPriceAnalyticsForm


class StockMixin(object):
    stock = None

    def dispatch(self, request, slug, **kwargs):
        try:
            self.stock = self.get_stock(slug)
        except Stock.DoesNotExist:
            raise Http404
        return super().dispatch(request, **kwargs)

    def get_stock(self, slug):
        return Stock.objects.get(slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock'] = self.stock
        return context


class JsonResponseMixin(object):
    serializer = None

    def get(self, request, **kwargs):
        if kwargs.get('api'):
            return JsonResponse(self._get_json_context_data(), safe=False)
        return super().get(request, **kwargs)

    def _get_json_context_data(self):
        queryset = self.get_queryset()
        if getattr(self, 'paginate_by', None):
            paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, self.paginate_by)
            return {
                'count': page.paginator.count,
                'next': self._get_next_link(page),
                'previous': self._get_previous_link(page),
                'results': self.serializer(queryset, many=True).data
            }
        return self.serializer(queryset, many=True).data

    def _get_next_link(self, page):
        if not page.has_next():
            return None
        url = self.request.build_absolute_uri()
        page_number = page.next_page_number()
        return replace_query_param(url, 'page', page_number)

    def _get_previous_link(self, page):
        if not page.has_previous():
            return None
        url = self.request.build_absolute_uri()
        page_number = page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, 'page')
        return replace_query_param(url, 'page', page_number)


class StockListView(JsonResponseMixin, ListView):
    model = Stock
    template_name = 'base/stock_list.html'
    serializer = StockSerializer


class StockDetailView(StockMixin, JsonResponseMixin, ListView):
    model = StockPrice
    template_name = 'base/stock_detail.html'
    serializer = StockPriceSerializer

    def get_queryset(self):
        return super().get_queryset().filter(stock=self.stock)


class InsiderTradeListView(StockMixin, JsonResponseMixin, ListView):
    model = InsiderTrade
    template_name = 'base/trade_list.html'
    serializer = InsiderTradeSerializer
    insider = None
    paginate_by = 100

    def dispatch(self, request, **kwargs):
        try:
            self.insider = self.get_insider(kwargs.pop('insider_id'))
        except Insider.DoesNotExist:
            raise Http404
        except KeyError:
            pass
        return super().dispatch(request, **kwargs)

    def get_insider(self, insider_id):
        return Insider.objects.get(id=insider_id)

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            insider__stock=self.stock
        ).select_related('insider')
        if self.insider:
            queryset = queryset.filter(insider=self.insider)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['insider'] = self.insider
        return context


class StockAnalyticsView(StockDetailView):
    serializer = StockPriceWithDeltaSerializer

    def get_queryset(self):
        form = self.get_form()
        queryset = super().get_queryset()
        if form.is_valid():
            return queryset.in_period(**form.cleaned_data).with_previous()
        return queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def get_form(self):
        return StockPriceAnalyticsForm(self.request.GET)


class StockDeltaView(StockMixin, JsonResponseMixin, TemplateView):
    template_name = 'base/delta_list.html'
    serializer = StockDeltaSerializer

    def get_queryset(self):
        form = self.get_form()
        if form.is_valid():
            return StockPrice.objects.delta(stock=self.stock, **form.cleaned_data)
        return StockPrice.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['delta_list'] = self.get_queryset()
        return context

    def get_form(self):
        return StockPriceDeltaForm(self.request.GET)
