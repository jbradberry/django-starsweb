from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^', include('starsweb.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
)
