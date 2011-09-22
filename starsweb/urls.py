from django.conf.urls.defaults import *


urlpatterns = patterns('starsweb.views',
    (r'^games/$', 'games_list'),
    (r'^games/(?P<slug>[-\w]+)/$', 'games_detail'),
    (r'^games/(?P<gameslug>[-\w]+)/race/(?P<slug>[-\w]+)/$', 'race_detail'),
)
