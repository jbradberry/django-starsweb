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

    def related_agents(self, realm, agent_type):
        if (agent_type.app_label, agent_type.model) == ('starsweb', 'race'):
            return realm.races.all()

    def has_perm(self, user, perm, obj):
        methodname = self.permissions.get(perm)
        if methodname is None:
            return False
        return getattr(self, methodname, None)(user, obj)

    def _is_host(self, user, obj):
        return obj.host == user

    def _is_active_ambassador(self, user, obj):
        return obj.ambassadors.filter(active=True, user=user).exists()

    def is_ready(self, generator):
        readys = set(r.agent.pk for r in generator.readies.all())
        return all(
            race.pk in readys
            for race in models.Race.objects.filter(game_id=generator.object_id,
                                                   player_number__isnull=False,
                                                   ambassadors__active=True,
                                                   is_ai=False)
        )

    def auto_generate(self, realm):
        realm.generate()

    def force_generate(self, realm):
        realm.generate()
