# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.conf import settings

urlpatterns = [
    url(r'^api/', include('finance.base.urls'), kwargs={'api': True}),
    url(r'^', include('finance.base.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_ROOT, document_root=settings.STATIC_ROOT)
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
