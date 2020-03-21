from __future__ import absolute_import
from django.contrib import admin
from starsweb.models import Game, Race, Ambassador, Turn, Score


class GameAdmin(admin.ModelAdmin):
    fields = ('name', 'slug', 'description', 'markup_type', 'host',
              'state', 'published')
    list_display = ('name', 'created', 'state', 'published')
    prepopulated_fields = {"slug": ("name",)}


class RaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'plural_name', 'game', 'player_number')
    ordering = ('game',)
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Game, GameAdmin)
admin.site.register(Race, RaceAdmin)
admin.site.register(Ambassador)
admin.site.register(Turn)
admin.site.register(Score)
