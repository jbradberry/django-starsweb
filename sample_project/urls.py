from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r'^', include('starsweb.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
)
