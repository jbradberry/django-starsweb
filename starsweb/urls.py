from django.conf.urls import patterns, url, include
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView
from django.conf import settings

from . import views


urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url=reverse_lazy('game_list'),
                                    permanent=False)),
    url(r'^game/$', views.GameListView.as_view(), name='game_list'),
    url(r'^game/(?P<slug>[-\w]+)/$', views.GameDetailView.as_view(),
        name='game_detail'),
    url(r'^game/(?P<game_slug>[-\w]+)/join/$', views.GameJoinView.as_view(),
        name='game_join'),
    url(r'^game/(?P<slug>[-\w]+)/score/$',
        views.ScoreGraphView.as_view(), name='score_graph'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<slug>[-\w]+)/$',
        views.RaceDetailView.as_view(), name='race_detail'),
    url(r'^game/(?P<game_slug>[-\w]+)/manage/(?P<race_slug>[-\w]+)/race/$',
        views.RaceUpdateView.as_view(), name='race_update'),
    url(r'^game/(?P<game_slug>[-\w]+)/manage/(?P<race_slug>[-\w]+)/ambassador/$',
        views.AmbassadorUpdateView.as_view(), name='ambassador_update'),
    url(r'^create/$', views.GameCreateView.as_view(), name='create_game'),
)

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += patterns('',
        (r'^game/(?P<realm_slug>[-\w]+)/news/',
         include('micropress.urls', namespace="starsweb",
                 app_name="micropress"),
         {'realm_content_type': 'starsweb.Game'}),
    )
