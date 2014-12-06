from . import models


class TurnGeneration(object):
    slug_field = 'slug'

    slug_kwarg = 'owner_slug'
    pk_kwarg = 'owner_pk'

    def _has_permission(self, user, owner):
        return owner.ambassadors.filter(active=True, user=user).exists()

    def has_pause_permission(self, user, owner):
        return self._has_permission(user, owner)

    def has_unpause_permission(self, user, owner):
        return self._has_permission(user, owner)

    def has_ready_permission(self, user, owner):
        return self._has_permission(user, owner)

    def has_unready_permission(self, user, owner):
        return self._has_permission(user, owner)

    def get_owner(self, realm, kw):
        filters = {}
        if self.slug_kwarg in kw:
            filters[self.slug_field] = kw[self.slug_kwarg]
        if self.pk_kwarg in kw:
            filters['pk'] = kw[self.pk_kwarg]

        qs = realm.races.filter(**filters)
        if qs:
            return qs[0]

    def auto_generate(self, realm):
        realm.generate()

    def force_generate(self, realm):
        realm.generate()
