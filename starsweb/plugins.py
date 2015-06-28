from django.contrib.contenttypes.models import ContentType

from . import models


class TurnGeneration(object):
    realm_types = {
        'starsgame': 'starsweb.game',
    }

    agent_types = {
        'starsrace': 'starsweb.race',
    }

    permissions = {
        'turngeneration.add_generator': '_is_host',
        'turngeneration.change_generator': '_is_host',
        'turngeneration.delete_generator': '_is_host',
        'turngeneration.add_generationrule': '_is_host',
        'turngeneration.change_generationrule': '_is_host',
        'turngeneration.delete_generationrule': '_is_host',
        'turngeneration.add_pause': '_is_active_ambassador',
        'turngeneration.change_pause': '_is_active_ambassador',
        'turngeneration.delete_pause': '_is_active_ambassador',
        'turngeneration.add_ready': '_is_active_ambassador',
        'turngeneration.change_ready': '_is_active_ambassador',
        'turngeneration.delete_ready': '_is_active_ambassador',
    }

    def related_agents(self, realm, agent_type=None):
        ct = ContentType.objects.get_for_model(models.Race)
        if agent_type is None:
            agent_type = ct
        if agent_type != ct:
            return
        return realm.races.filter(player_number__isnull=False,
                                  ambassadors__active=True,
                                  is_ai=False)

    def _is_host(self, user, obj):
        return obj.host == user

    def _is_active_ambassador(self, user, obj):
        return obj.ambassadors.filter(active=True, user=user).exists()

    def auto_generate(self, realm):
        realm.generate()

    def force_generate(self, realm):
        realm.generate()
