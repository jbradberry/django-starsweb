from django.views.generic.list_detail import object_list, object_detail
from django.db.models import Max
import models


def game_list(request, state=None, template_object_name='game', **kwargs):
    qs = models.Game.objects.select_related('turn').annotate(
        generated=Max('turn__generated')).order_by('-generated')
    if state is None:
        state = request.GET.get('state', None)
    if state is not None:
        qs = qs.filter(state=state)
    return object_list(request, qs, template_object_name=template_object_name,
                       **kwargs)


def game_detail(request, template_object_name='game', **kwargs):
    qs = models.Game.objects.all()
    return object_detail(request, qs,
                         template_object_name=template_object_name, **kwargs)


def race_detail(request, gameslug, template_object_name='race', **kwargs):
    qs = models.Race.objects.filter(game__slug=gameslug)
    return object_detail(request, qs,
                         template_object_name=template_object_name, **kwargs)
