# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Race.is_ai'
        db.add_column(u'starsweb_race', 'is_ai',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Race.official_racefile'
        db.add_column(u'starsweb_race', 'official_racefile',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='official_race', null=True, to=orm['starsweb.StarsFile']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Race.is_ai'
        db.delete_column(u'starsweb_race', 'is_ai')

        # Deleting field 'Race.official_racefile'
        db.delete_column(u'starsweb_race', 'official_racefile_id')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'starsweb.ambassador': {
            'Meta': {'unique_together': "(('race', 'user'),)", 'object_name': 'Ambassador'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'race': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ambassadors'", 'to': u"orm['starsweb.Race']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'starsweb.game': {
            'Meta': {'object_name': 'Game'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stars_games'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mapfile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['starsweb.StarsFile']", 'null': 'True'}),
            'markup_type': ('django.db.models.fields.CharField', [], {'default': "'markdown'", 'max_length': '32'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'S'", 'max_length': '1'})
        },
        u'starsweb.gameoptions': {
            'Meta': {'object_name': 'GameOptions'},
            'accelerated_bbs': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ai_players': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '64', 'blank': 'True'}),
            'capital_ships': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'computer_alliances': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'exceeds_nearest_score': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'file_contents': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'galaxy_clumping': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'game': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'options'", 'unique': 'True', 'to': u"orm['starsweb.Game']"}),
            'highest_score_after_years': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maximum_minerals': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'min_turns_to_win': ('django.db.models.fields.IntegerField', [], {'default': '50'}),
            'num_criteria': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'percent_planets': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'production': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'public_scores': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'random_events': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slow_tech': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'starting_distance': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'tech_fields': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'tech_level': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'universe_density': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'universe_size': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        u'starsweb.gamerace': {
            'Meta': {'object_name': 'GameRace'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'race': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'official'", 'unique': 'True', 'to': u"orm['starsweb.Race']"}),
            'racefile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['starsweb.StarsFile']"})
        },
        u'starsweb.race': {
            'Meta': {'unique_together': "(('game', 'slug'), ('game', 'name'), ('game', 'plural_name'), ('game', 'player_number'))", 'object_name': 'Race'},
            'game': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'races'", 'to': u"orm['starsweb.Game']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_ai': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'official_racefile': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'official_race'", 'null': 'True', 'to': u"orm['starsweb.StarsFile']"}),
            'player_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'plural_name': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'racefile': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'race'", 'null': 'True', 'to': u"orm['starsweb.StarsFile']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '16'})
        },
        u'starsweb.score': {
            'Meta': {'ordering': "('-turn', 'race')", 'unique_together': "(('turn', 'race', 'section'),)", 'object_name': 'Score'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'race': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scores'", 'to': u"orm['starsweb.Race']"}),
            'section': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scores'", 'to': u"orm['starsweb.Turn']"}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'starsweb.starsfile': {
            'Meta': {'object_name': 'StarsFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'upload_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'starsfiles'", 'null': 'True', 'to': u"orm['auth.User']"})
        },
        u'starsweb.turn': {
            'Meta': {'ordering': "('-generated',)", 'object_name': 'Turn'},
            'game': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'turns'", 'to': u"orm['starsweb.Game']"}),
            'generated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        u'starsweb.userrace': {
            'Meta': {'unique_together': "(('user', 'identifier'),)", 'object_name': 'UserRace'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'racefile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['starsweb.StarsFile']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'racepool'", 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['starsweb']