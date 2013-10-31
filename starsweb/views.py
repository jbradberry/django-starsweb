from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.db.models import Max

from . import models
from . import forms


class GameListView(ListView):
    queryset = models.Game.objects.select_related('turn').annotate(
        generated=Max('turn__generated')).order_by('-generated', '-created')

    state = None

    def get_queryset(self):
        queryset = super(GameListView, self).get_queryset()

        state = self.kwargs.get('state', self.state)

        if state is not None:
            queryset = queryset.filter(state=state)
        return queryset


class GameDetailView(DetailView):
    model = models.Game


class GameCreateView(CreateView):
    model = models.Game
    form_class = forms.CreateGameForm

    @method_decorator(permission_required('starsweb.add_game'))
    def dispatch(self, *args, **kwargs):
        return super(GameCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.host = self.request.user
        return super(GameCreateView, self).form_valid(form)


class RaceDetailView(DetailView):
    model = models.Race

    def get_queryset(self):
        queryset = super(RaceDetailView, self).get_queryset()

        return queryset.filter(game__slug=self.kwargs.get('gameslug'))
