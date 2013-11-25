from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.db.models import Max
import json

from . import models
from . import forms


class GameListView(ListView):
    queryset = models.Game.objects.select_related('turn').annotate(
        generated=Max('turns__generated')).order_by('-generated', '-created')

    state = None

    def get_queryset(self):
        queryset = super(GameListView, self).get_queryset()

        state = self.kwargs.get('state', self.state)

        if state is not None:
            queryset = queryset.filter(state=state)
        return queryset


class GameDetailView(DetailView):
    model = models.Game

    def get_context_data(self, **kwargs):
        context = super(GameDetailView, self).get_context_data(**kwargs)
        scores = {}
        turn = self.object.current_turn
        if turn:
            scores.update(
                turn.scores.filter(section=models.Score.SCORE
                                   ).values_list('race__plural_name', 'value'))
        context['races'] = sorted(((race, scores.get(str(race)))
                                   for race in self.object.races.all()),
                                  key=lambda (r, s): (s, str(r), r),
                                  reverse=True)
        return context


class GameCreateView(CreateView):
    model = models.Game
    form_class = forms.CreateGameForm
    template_name_suffix = '_create_form'

    @method_decorator(permission_required('starsweb.add_game'))
    def dispatch(self, *args, **kwargs):
        return super(GameCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.host = self.request.user
        return super(GameCreateView, self).form_valid(form)


class ScoreGraphView(DetailView):
    model = models.Game
    template_name = 'starsweb/score_graph.html'

    def get_context_data(self, **kwargs):
        context = super(ScoreGraphView, self).get_context_data(**kwargs)
        section_name = self.request.GET.get('section')
        if section_name:
            section = getattr(models.Score, section_name.upper(), None)
        else:
            section = models.Score.SCORE

        scores = models.Score.objects.select_related(
            'turn', 'race'
        ).filter(
            turn__game=self.object, section=section
        ).values('turn__year', 'race__plural_name', 'value')

        context['races'] = json.dumps(
            list(self.object.races.values_list('plural_name', flat=True))
        )

        context['scores'] = json.dumps([{'year': score['turn__year'],
                                         'race': score['race__plural_name'],
                                         'value': score['value']}
                                         for score in scores])
        context['scoretype'] = dict(models.Score.SECTIONS).get(section, '')
        return context


class RaceDetailView(DetailView):
    model = models.Race

    def get_queryset(self):
        queryset = super(RaceDetailView, self).get_queryset()

        return queryset.filter(game__slug=self.kwargs.get('game_slug'))
