from django.views.generic.list_detail import object_list, object_detail
import models


def games_list(request, state=None, **kwargs):
    qs = models.Game.objects.all()
    if state is None:
        state = request.GET.get('state', None)
    if state is not None:
        qs = qs.filter(state=state)
    return object_list(request, qs, **kwargs)


def games_detail(request, **kwargs):
    qs = models.Game.objects.all()
    return object_detail(request, qs, **kwargs)


def race_detail(request, gameslug, **kwargs):
    qs = models.Race.objects.filter(game__slug=gameslug)
    return object_detail(request, qs, **kwargs)
