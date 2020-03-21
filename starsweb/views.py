from __future__ import absolute_import
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView, TemplateView, View)
from django.contrib.auth.decorators import permission_required, login_required
from django.utils.decorators import method_decorator
from django.template.defaultfilters import slugify
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.core.files.base import ContentFile
from django.contrib import messages
from django.db.models import Max

from sendfile import sendfile
from starslib import base
import json

from . import models
from . import forms
from six.moves import range


class GameListView(ListView):
    queryset = models.Game.objects.prefetch_related('turns').annotate(
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
        context = {}

        scores = {}
        turn = self.object.current_turn
        if turn:
            scores.update(
                turn.scores.filter(section=models.Score.SCORE
                                   ).values_list('race__plural_name', 'value'))
        context['races'] = sorted(((race, scores.get(str(race)))
                                   for race in self.object.races.all()),
                                  key=lambda r_s: (r_s[1] if r_s[1] is None else -r_s[1],
                                                      r_s[0].player_number, r_s[0].pk))
        context.update(kwargs)
        return super(GameDetailView, self).get_context_data(**context)


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


class ParentGameMixin(object):
    context_game_name = 'game'

    game_slug_field = 'slug'
    pk_game_kwarg = 'game_pk'
    slug_game_kwarg = 'game_slug'

    def get_game(self):
        game_queryset = models.Game.objects.all()

        pk = self.kwargs.get(self.pk_game_kwarg, None)
        slug = self.kwargs.get(self.slug_game_kwarg, None)
        if pk is not None:
            game_queryset = game_queryset.filter(pk=pk)
        elif slug is not None:
            game_queryset = game_queryset.filter(
                **{self.game_slug_field: slug})
        else:
            raise AttributeError(
                "{0} must be called with either a game pk or a slug.".format(
                    self.__class__.__name__))

        try:
            return game_queryset.get()
        except models.Game.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        context = {self.context_game_name: self.game}
        context.update(kwargs)
        return super(ParentGameMixin, self).get_context_data(**context)


class ParentRaceMixin(ParentGameMixin):
    context_race_name = 'race'

    race_slug_field = 'slug'
    pk_race_kwarg = 'race_pk'
    slug_race_kwarg = 'race_slug'

    def get_race(self):
        race_queryset = self.game.races.all()

        pk = self.kwargs.get(self.pk_race_kwarg, None)
        slug = self.kwargs.get(self.slug_race_kwarg, None)
        if pk is not None:
            race_queryset = race_queryset.filter(pk=pk)
        elif slug is not None:
            race_queryset = race_queryset.filter(
                **{self.race_slug_field: slug})
        else:
            raise AttributeError(
                "{0} must be called with either a race pk or a slug.".format(
                    self.__class__.__name__))

        try:
            return race_queryset.get()
        except models.Race.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        context = {self.context_race_name: self.race}
        context.update(kwargs)
        return super(ParentRaceMixin, self).get_context_data(**context)


class GameMapDownload(ParentGameMixin, View):
    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.mapfile is None:
            raise Http404
        return sendfile(
            self.request, self.game.mapfile.file.path, attachment=True,
            attachment_filename='{name}.xy'.format(name=self.game.slug[:8]))


class GameAdminView(ParentGameMixin, UpdateView):
    model = models.GameOptions
    form_class = forms.GameOptionsForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(GameAdminView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('game_admin', kwargs={'game_slug': self.game.slug})

    def get_object(self):
        try:
            return self.game.options
        except models.GameOptions.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.host != self.request.user:
            raise PermissionDenied
        return super(GameAdminView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.host != self.request.user:
            raise PermissionDenied
        return super(GameAdminView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.game = self.game
        messages.success(self.request, "Game configuration successfully saved.")
        return super(GameAdminView, self).form_valid(form)


class GameJoinView(ParentGameMixin, CreateView):
    template_name = 'starsweb/game_join_form.html'

    form_class = forms.RaceForm
    second_form_class = forms.AmbassadorForm
    context_second_form_name = 'ambassador_form'

    def get_success_url(self):
        return self.game.get_absolute_url()

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.state != 'S':
            raise PermissionDenied

        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        second_form = self.get_form(self.second_form_class)
        second_form.prefix = 'ambassador'

        return self.render_to_response(
            self.get_context_data(
                **{'form': form, self.context_second_form_name: second_form}))

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.state != 'S':
            raise PermissionDenied

        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.instance.game = self.game
        second_form = self.get_form(self.second_form_class)
        second_form.prefix = 'ambassador'

        if form.is_valid() and second_form.is_valid():
            response = self.form_valid(form)
            second_form.instance.race = self.object
            second_form.instance.user = self.request.user
            second_form.save()
            return response
        else:
            return self.form_invalid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(GameJoinView, self).dispatch(*args, **kwargs)


class RaceUpdateView(ParentGameMixin, UpdateView):
    model = models.Race
    form_class = forms.RaceForm

    slug_url_kwarg = 'race_slug'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RaceUpdateView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return self.game.get_absolute_url()

    def get_queryset(self):
        return self.game.races.all()

    def get_object(self, queryset=None):
        race = super(RaceUpdateView, self).get_object()
        if not race.ambassadors.filter(user=self.request.user,
                                       active=True).exists():
            raise PermissionDenied
        return race

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.state != 'S':
            raise PermissionDenied
        return super(RaceUpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.state != 'S':
            raise PermissionDenied
        return super(RaceUpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        racefile = form.instance.racefile

        if racefile:
            sf = base.StarsFile()
            try:
                racefile.file.open()
                data = racefile.file.read()
                sf.bytes = data
            finally:
                racefile.file.close()

            race_struct = sf.structs[1]
            name = race_struct.race_name
            plural_name = race_struct.plural_race_name
            altered = False

            if name != form.instance.name or plural_name != form.instance.plural_name:
                messages.info(
                    self.request,
                    "The attached race file's name or plural name has been"
                    " adjusted to match your race's name and plural name."
                )
                altered = True

            if altered:
                race_struct.race_name = form.instance.name
                race_struct.plural_race_name = form.instance.plural_name

                racefile.file.save('', ContentFile(sf.bytes))

        messages.success(
            self.request,
            "The race name and plural name have successfully been changed.")
        return super(RaceUpdateView, self).form_valid(form)


class AmbassadorUpdateView(ParentRaceMixin, UpdateView):
    model = models.Ambassador
    form_class = forms.AmbassadorForm

    def get_success_url(self):
        return self.game.get_absolute_url()

    def get_queryset(self):
        return self.race.ambassadors.filter(user=self.request.user,
                                            active=True)

    def get_object(self):
        try:
            return self.get_queryset().get()
        except models.Ambassador.DoesNotExist:
            raise PermissionDenied

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.state == 'F':
            raise PermissionDenied
        self.race = self.get_race()
        return super(AmbassadorUpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.state == 'F':
            raise PermissionDenied
        self.race = self.get_race()
        return super(AmbassadorUpdateView, self).post(request, *args, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AmbassadorUpdateView, self).dispatch(*args, **kwargs)


class RacePageView(ParentRaceMixin, DetailView):
    def get_object(self, queryset=None):
        if self.kwargs.get('slug') is None:
            if self.race.homepage is not None:
                return self.race.homepage
            else:
                raise Http404
        return super(RacePageView, self).get_object(queryset)

    def get_queryset(self):
        return self.race.racepages.all()

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        return super(RacePageView, self).get(request, *args, **kwargs)


class RacePageCreate(ParentRaceMixin, CreateView):
    model = models.RacePage
    form_class = forms.RacePageForm

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()

        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state == 'F':
            raise PermissionDenied

        return super(RacePageCreate, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()

        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state == 'F':
            raise PermissionDenied

        return super(RacePageCreate, self).post(request, *args, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RacePageCreate, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.race = self.race
        response = super(RacePageCreate, self).form_valid(form)
        if not self.race.homepage or form.cleaned_data['set_as_homepage']:
            self.race.homepage = self.object
            self.race.save()
        return response


class RacePageUpdate(ParentRaceMixin, UpdateView):
    model = models.RacePage
    form_class = forms.RacePageForm

    def get_queryset(self):
        return self.race.racepages.all()

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()

        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state == 'F':
            raise PermissionDenied

        return super(RacePageUpdate, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()

        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state == 'F':
            raise PermissionDenied

        return super(RacePageUpdate, self).post(request, *args, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RacePageUpdate, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        response = super(RacePageUpdate, self).form_valid(form)
        if not self.race.homepage or form.cleaned_data['set_as_homepage']:
            self.race.homepage = self.object
            self.race.save()
        return response


class RacePageDelete(ParentRaceMixin, DeleteView):
    model = models.RacePage

    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'slug': self.game.slug})

    def get_queryset(self):
        return self.race.racepages.all()

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()

        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state == 'F':
            raise PermissionDenied

        return super(RacePageDelete, self).get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()

        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state == 'F':
            raise PermissionDenied

        self.race.homepage = None
        self.race.save()

        return super(RacePageDelete, self).delete(request, *args, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RacePageDelete, self).dispatch(*args, **kwargs)


class RaceDashboardView(ParentRaceMixin, TemplateView):
    template_name = 'starsweb/race_dashboard.html'

    def get_ambassador(self):
        try:
            return self.race.ambassadors.get(user=self.request.user,
                                             active=True)
        except models.Ambassador.DoesNotExist:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = {'game': self.game,
                   'race': self.race,
                   'ambassador': self.ambassador}
        if self.game.state == 'S':
            context.update(race_form=forms.RaceForm(instance=self.race),
                           raceupload_form=forms.RaceFileForm(),
                           racechoose_form=forms.ChooseUserRaceForm(
                               user=self.request.user))
        if self.game.state != 'F':
            context.update(
                ambassador_form=forms.AmbassadorForm(instance=self.ambassador))
        context.update(kwargs)
        return super(RaceDashboardView, self).get_context_data(**context)

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        self.ambassador = self.get_ambassador()
        return super(RaceDashboardView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RaceDashboardView, self).dispatch(*args, **kwargs)


class ScoreGraphView(DetailView):
    model = models.Game
    template_name = 'starsweb/score_graph.html'

    def get_context_data(self, **kwargs):
        scores = models.Score.objects.select_related(
            'turn', 'race'
        ).filter(
            turn__game=self.object
        ).values('section', 'turn__year', 'race__plural_name', 'value')

        races = list(self.object.races.values_list(
            'plural_name', flat=True).order_by('id'))

        year_min, year_max = 2400, 2400
        if scores:
            year_min = min(x['turn__year'] for x in scores)
            year_max = max(x['turn__year'] for x in scores)

        score_data = {}
        for item in scores:
            section_set = score_data.setdefault(
                models.Score.TOKEN_VALUES[item['section']], {})
            race_scores = section_set.setdefault(
                item['race__plural_name'],
                [None for x in range(year_min, year_max+1)])
            race_scores[item['turn__year'] - year_min] = item['value']

        context = {
            'races': json.dumps(races),
            'visible_races': json.dumps(
                self.request.GET.getlist('races[]', [])),
            'section': self.request.GET.get('section', 'score'),
            'sections': models.Score.NAMES,
            'json_sections': json.dumps(dict(models.Score.NAMES)),
            'from_year': self.request.GET.get('from_year', ''),
            'to_year': self.request.GET.get('to_year', ''),
            'scores': json.dumps(score_data),
            'year_min': year_min,
            'year_max': year_max,
        }
        context.update(kwargs)
        return super(ScoreGraphView, self).get_context_data(**context)


class UserDashboard(TemplateView):
    template_name = 'starsweb/user_dashboard.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserDashboard, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {
            'userraces': models.UserRace.objects.filter(
                user=self.request.user),
            'races': models.Race.objects.filter(
                ambassadors__user=self.request.user,
                official_racefile__isnull=False),
            'new_form': forms.UserRaceForm(),
            'upload_form': forms.RaceFileForm()
        }
        context.update(kwargs)
        return super(UserDashboard, self).get_context_data(**context)


class UserRaceCreate(CreateView):
    model = models.UserRace
    form_class = forms.UserRaceForm
    success_url = reverse_lazy('user_dashboard')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserRaceCreate, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(UserRaceCreate, self).get_form_kwargs()
        kwargs['instance'] = self.model(user=self.request.user)
        return kwargs


class UserRaceUpdate(UpdateView):
    model = models.UserRace
    form_class = forms.UserRaceForm
    success_url = reverse_lazy('game_list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserRaceUpdate, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user != self.request.user:
            raise PermissionDenied
        return super(UserRaceUpdate, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user != self.request.user:
            raise PermissionDenied
        return super(UserRaceUpdate, self).post(request, *args, **kwargs)


class UserRaceDelete(DeleteView):
    model = models.UserRace
    success_url = reverse_lazy('game_list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserRaceDelete, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user != self.request.user:
            raise PermissionDenied
        return super(UserRaceDelete, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user != self.request.user:
            raise PermissionDenied
        return super(UserRaceDelete, self).post(request, *args, **kwargs)


class RaceFileBind(ParentGameMixin, UpdateView):
    model = models.Race
    form_class = forms.ChooseUserRaceForm
    success_url = reverse_lazy('game_list')

    slug_url_kwarg = 'race_slug'

    def get_success_url(self):
        return self.game.get_absolute_url()

    def get_queryset(self):
        return self.game.races.all()

    def get_object(self, queryset=None):
        race = super(RaceFileBind, self).get_object()
        if not race.ambassadors.filter(user=self.request.user,
                                       active=True).exists():
            raise PermissionDenied
        return race

    def get_form_kwargs(self):
        kwargs = super(RaceFileBind, self).get_form_kwargs()
        kwargs.update(user=self.request.user)
        return kwargs

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RaceFileBind, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.state != 'S':
            raise PermissionDenied
        return super(RaceFileBind, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        if self.game.state != 'S':
            raise PermissionDenied
        return super(RaceFileBind, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        racefile = form.instance.racefile

        if racefile:
            sf = base.StarsFile()
            try:
                racefile.file.open()
                data = racefile.file.read()
                sf.bytes = data
            finally:
                racefile.file.close()

            race_struct = sf.structs[1]
            name = race_struct.race_name
            plural_name = race_struct.plural_race_name
            altered = False

            if name != self.object.name or plural_name != self.object.plural_name:
                messages.info(
                    self.request,
                    "The attached race file's name or plural name has been"
                    " adjusted to match your race's name and plural name.")

                altered = True

            if altered:
                race_struct.race_name = self.object.name
                race_struct.plural_race_name = self.object.plural_name

                content = sf.bytes
            else:
                content = data

            new_starsfile = models.StarsFile(
                upload_user=racefile.upload_user,
                type=racefile.type,
            )
            new_starsfile.save()
            new_starsfile.file.save('', ContentFile(content))

            form.instance.racefile = new_starsfile
            messages.success(self.request,
                             "The race file has successfully been attached.")
        else:
            messages.success(self.request,
                             "The race file has successfully been unattached.")

        return super(RaceFileBind, self).form_valid(form)


class UserRaceMixin(object):
    def get_userrace(self):
        pk = self.kwargs.get('pk', None)

        try:
            userrace = models.UserRace.objects.get(pk=pk)
        except models.UserRace.DoesNotExist:
            raise Http404

        return userrace


class UserRaceDownload(UserRaceMixin, View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserRaceDownload, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.userrace = self.get_userrace()
        if self.userrace.user != self.request.user:
            raise PermissionDenied
        if self.userrace.racefile is None:
            raise Http404
        return sendfile(
            self.request, self.userrace.racefile.file.path, attachment=True,
            attachment_filename='{name}.r1'.format(
                name=slugify(self.userrace.identifier)[:8])
        )


class UserRaceUpload(UserRaceMixin, CreateView):
    form_class = forms.RaceFileForm
    template_name = 'starsweb/racefile_upload.html'
    success_url = reverse_lazy('game_list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserRaceUpload, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.userrace = self.get_userrace()
        if self.userrace.user != self.request.user:
            raise PermissionDenied
        return super(UserRaceUpload, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.userrace = self.get_userrace()
        if self.userrace.user != self.request.user:
            raise PermissionDenied
        response = super(UserRaceUpload, self).post(request, *args, **kwargs)
        self.userrace.racefile = self.object
        self.userrace.save()
        return response

    def form_valid(self, form):
        form.instance.upload_user = self.request.user

        race_struct = form.stars_file.structs[1]
        name = race_struct.race_name
        plural_name = race_struct.plural_race_name
        altered = False

        if name.strip() != name or plural_name.strip() != plural_name:
            messages.warning(
                self.request,
                "The uploaded race file's name or plural name had extra"
                " whitespace before or after the name. The file has been"
                " edited to fix this.")

            altered = True
            name = name.strip()
            plural_name = plural_name.strip()

        prepended_the = False
        if name.lower().startswith("the "):
            altered, prepended_the = True, True
            name = name[4:].strip()

        if plural_name.lower().startswith("the "):
            altered, prepended_the = True, True
            plural_name = plural_name[4:].strip()

        if prepended_the:
            messages.warning(
                self.request,
                "The uploaded race file's name or plural name had the word"
                " 'The' before it. The file has been edited to fix this.")

        if altered:
            race_struct.race_name = name
            race_struct.plural_race_name = plural_name

            content = ContentFile(form.stars_file.bytes)
            form.instance.file.file = content

        messages.success(
            self.request,
            "The race file has successfully been uploaded."
        )
        return super(UserRaceUpload, self).form_valid(form)


class RaceFileDownload(ParentRaceMixin, View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RaceFileDownload, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user).exists():
            raise PermissionDenied

        if self.race.official_racefile is not None:
            racefile = self.race.official_racefile
        elif self.race.racefile is not None:
            racefile = self.race.racefile
        else:
            raise Http404

        return sendfile(
            self.request, self.race.racefile.file.path, attachment=True,
            attachment_filename='{name}.r1'.format(name=self.race.slug))


class RaceFileUpload(ParentRaceMixin, CreateView):
    form_class = forms.RaceFileForm
    template_name = 'starsweb/racefile_upload.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RaceFileUpload, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return self.game.get_absolute_url()

    def form_valid(self, form):
        form.instance.upload_user = self.request.user

        race_struct = form.stars_file.structs[1]
        name = race_struct.race_name
        plural_name = race_struct.plural_race_name
        altered = False

        if name != self.race.name or plural_name != self.race.plural_name:
            messages.info(
                self.request,
                "The uploaded race file's name or plural name has been"
                " adjusted to match your race's name and plural name.")

            altered = True

        if altered:
            race_struct.race_name = self.race.name
            race_struct.plural_race_name = self.race.plural_name

            content = ContentFile(form.stars_file.bytes)
            form.instance.file.file = content

        response = super(RaceFileUpload, self).form_valid(form)
        self.race.racefile = self.object
        self.race.save()
        messages.success(
            self.request,
            "The race file has successfully been uploaded."
        )
        return response

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state != 'S':
            raise PermissionDenied
        return super(RaceFileUpload, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state != 'S':
            raise PermissionDenied
        return super(RaceFileUpload, self).post(request, *args, **kwargs)


class StateFileDownload(ParentRaceMixin, View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(StateFileDownload, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user).exists():
            raise PermissionDenied

        current = self.game.current_turn
        if current is None:
            raise Http404

        raceturn = current.raceturns.filter(race=self.race, mfile__isnull=False)
        if not raceturn:
            raise Http404

        raceturn = raceturn.get()

        return sendfile(
            self.request, raceturn.mfile.file.path, attachment=True,
            attachment_filename='{name}.m{num}'.format(
                name=self.game.slug[:8], num=self.race.player_number + 1))


class OrderFileDownload(ParentRaceMixin, View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrderFileDownload, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user).exists():
            raise PermissionDenied

        current = self.game.current_turn
        if current is None:
            raise Http404

        raceturn = current.raceturns.filter(race=self.race, xfile__isnull=False)
        if not raceturn:
            raise Http404

        raceturn = raceturn.get()

        return sendfile(
            self.request, raceturn.xfile.file.path, attachment=True,
            attachment_filename='{name}.x{num}'.format(
                name=self.game.slug[:8], num=self.race.player_number + 1))


class OrderFileUpload(ParentRaceMixin, CreateView):
    form_class = forms.OrderFileForm
    template_name = 'starsweb/orderfile_upload.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrderFileUpload, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return self.game.get_absolute_url()

    def form_valid(self, form):
        form.instance.upload_user = self.request.user

        response = super(OrderFileUpload, self).form_valid(form)
        self.raceturn.xfile = self.object
        self.raceturn.save()

        messages.success(
            self.request,
            "The order file has successfully been uploaded."
        )
        return response

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state not in ('A', 'P'):
            raise PermissionDenied

        self.current_turn = self.game.current_turn
        if self.current_turn is None:
            raise Http404

        raceturn = self.current_turn.raceturns.filter(race=self.race)
        if not raceturn:
            raise Http404
        self.raceturn = raceturn.get()

        return super(OrderFileUpload, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state not in ('A', 'P'):
            raise PermissionDenied

        self.current_turn = self.game.current_turn
        if self.current_turn is None:
            raise Http404

        raceturn = self.current_turn.raceturns.filter(race=self.race)
        if not raceturn:
            raise Http404
        self.raceturn = raceturn.get()

        return super(OrderFileUpload, self).post(request, *args, **kwargs)


class HistoryFileDownload(ParentRaceMixin, View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HistoryFileDownload, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user).exists():
            raise PermissionDenied

        current = self.game.current_turn
        if current is None:
            raise Http404

        raceturn = current.raceturns.filter(race=self.race, hfile__isnull=False)
        if not raceturn:
            raise Http404

        raceturn = raceturn.get()

        return sendfile(
            self.request, raceturn.hfile.file.path, attachment=True,
            attachment_filename='{name}.h{num}'.format(
                name=self.game.slug[:8], num=self.race.player_number + 1))


class HistoryFileUpload(ParentRaceMixin, CreateView):
    form_class = forms.HistoryFileForm
    template_name = 'starsweb/historyfile_upload.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HistoryFileUpload, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return self.game.get_absolute_url()

    def form_valid(self, form):
        form.instance.upload_user = self.request.user

        response = super(HistoryFileUpload, self).form_valid(form)
        self.raceturn.hfile = self.object
        self.raceturn.save()

        messages.success(
            self.request,
            "The history file has successfully been uploaded."
        )
        return response

    def get(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state not in ('A', 'P'):
            raise PermissionDenied

        self.current_turn = self.game.current_turn
        if self.current_turn is None:
            return Http404

        raceturn = self.current_turn.raceturns.filter(race=self.race)
        if not raceturn:
            raise Http404
        self.raceturn = raceturn.get()

        return super(HistoryFileUpload, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.game = self.get_game()
        self.race = self.get_race()
        if not self.race.ambassadors.filter(user=self.request.user,
                                            active=True).exists():
            raise PermissionDenied
        if self.game.state not in ('A', 'P'):
            raise PermissionDenied

        self.current_turn = self.game.current_turn
        if self.current_turn is None:
            return Http404

        raceturn = self.current_turn.raceturns.filter(race=self.race)
        if not raceturn:
            raise Http404
        self.raceturn = raceturn.get()

        return super(HistoryFileUpload, self).post(request, *args, **kwargs)
