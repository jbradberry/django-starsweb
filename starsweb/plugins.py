from . import models


class TurnGeneration(object):
    def get_owner(self, realm, user, session):
        qs = models.Race.objects.filter(game=realm, ambassadors__user=user)
        name = session.get('name')
        if name:
            qs = qs.filter(name=name)
        if qs:
            return qs[0]

    def auto_generate(self, realm):
        realm.generate()

    def force_generate(self, realm):
        realm.generate()
