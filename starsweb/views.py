from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import permission_required
from django.db.models import Max
from django.shortcuts import redirect
import models
from forms import CreateGameForm, additional_forms


def game_list(request, state=None, template_object_name='game', **kwargs):
    qs = models.Game.objects.select_related('turn').annotate(
        generated=Max('turn__generated')).order_by('-generated', '-created')
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


@permission_required('starsweb.add_game')
def create_game(request):
    gameform = CreateGameForm(request.POST or None,
                              instance=models.Game(host=request.user))
    context = {'gameform': gameform}
    forms = additional_forms(request.POST or None)
    context.update(forms)
    if (gameform.is_valid()
        # each subform doesn't have to be valid if we are not creating it
        and all(not gameform.cleaned_data.get("create_{0}".format(name), True)
                or f.is_valid()
                for name, f in forms.iteritems())
        ):
        game = gameform.save()
        for name, f in forms.iteritems():
            if not gameform.cleaned_data.get("create_{0}".format(name), True):
                continue
            obj = f.save(commit=False)
            if not obj: continue
            obj.realm = game
            obj.save()
        return redirect('starsweb_game_list')
    return direct_to_template(request, 'starsweb/create_game.html',
                              extra_context=context)


def race_detail(request, gameslug, template_object_name='race', **kwargs):
    qs = models.Race.objects.filter(game__slug=gameslug)
    return object_detail(request, qs,
                         template_object_name=template_object_name, **kwargs)
