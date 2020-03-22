from django.conf.urls import include, url


urlpatterns = [
    url(r'^', include('starsweb.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
]
