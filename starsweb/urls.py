from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('starsweb.views',
    (r'^games/$', 'game_list'),
    (r'^games/(?P<slug>[-\w]+)/$', 'game_detail'),
    (r'^games/(?P<gameslug>[-\w]+)/race/(?P<slug>[-\w]+)/$', 'race_detail'),
)

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += patterns('',
        (r'^games/(?P<gameslug>[-\w]+)/news/', include('micropress.urls')),
    )
