# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Game'
        db.create_table(u'starsweb_game', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('description_html', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('markup_type', self.gf('django.db.models.fields.CharField')(default='markdown', max_length=32)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(related_name='stars_games', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='S', max_length=1)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'starsweb', ['Game'])

        # Adding model 'Race'
        db.create_table(u'starsweb_race', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(related_name='races', to=orm['starsweb.Game'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('plural_name', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=16)),
            ('player_number', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'starsweb', ['Race'])

        # Adding unique constraint on 'Race', fields ['game', 'slug']
        db.create_unique(u'starsweb_race', ['game_id', 'slug'])

        # Adding unique constraint on 'Race', fields ['game', 'name']
        db.create_unique(u'starsweb_race', ['game_id', 'name'])

        # Adding unique constraint on 'Race', fields ['game', 'plural_name']
        db.create_unique(u'starsweb_race', ['game_id', 'plural_name'])

        # Adding unique constraint on 'Race', fields ['game', 'player_number']
        db.create_unique(u'starsweb_race', ['game_id', 'player_number'])

        # Adding model 'Ambassador'
        db.create_table(u'starsweb_ambassador', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('race', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ambassadors', to=orm['starsweb.Race'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'starsweb', ['Ambassador'])

        # Adding model 'Turn'
        db.create_table(u'starsweb_turn', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(related_name='turns', to=orm['starsweb.Game'])),
            ('year', self.gf('django.db.models.fields.IntegerField')()),
            ('generated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'starsweb', ['Turn'])

        # Adding model 'Score'
        db.create_table(u'starsweb_score', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('turn', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scores', to=orm['starsweb.Turn'])),
            ('race', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scores', to=orm['starsweb.Race'])),
            ('section', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'starsweb', ['Score'])

        # Adding unique constraint on 'Score', fields ['turn', 'race', 'section']
        db.create_unique(u'starsweb_score', ['turn_id', 'race_id', 'section'])


    def backwards(self, orm):
        # Removing unique constraint on 'Score', fields ['turn', 'race', 'section']
        db.delete_unique(u'starsweb_score', ['turn_id', 'race_id', 'section'])

        # Removing unique constraint on 'Race', fields ['game', 'player_number']
        db.delete_unique(u'starsweb_race', ['game_id', 'player_number'])

        # Removing unique constraint on 'Race', fields ['game', 'plural_name']
        db.delete_unique(u'starsweb_race', ['game_id', 'plural_name'])

        # Removing unique constraint on 'Race', fields ['game', 'name']
        db.delete_unique(u'starsweb_race', ['game_id', 'name'])

        # Removing unique constraint on 'Race', fields ['game', 'slug']
        db.delete_unique(u'starsweb_race', ['game_id', 'slug'])

        # Deleting model 'Game'
        db.delete_table(u'starsweb_game')

        # Deleting model 'Race'
        db.delete_table(u'starsweb_race')

        # Deleting model 'Ambassador'
        db.delete_table(u'starsweb_ambassador')

        # Deleting model 'Turn'
        db.delete_table(u'starsweb_turn')

        # Deleting model 'Score'
        db.delete_table(u'starsweb_score')


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
            'Meta': {'object_name': 'Ambassador'},
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
            'markup_type': ('django.db.models.fields.CharField', [], {'default': "'markdown'", 'max_length': '32'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'S'", 'max_length': '1'})
        },
        u'starsweb.race': {
            'Meta': {'unique_together': "(('game', 'slug'), ('game', 'name'), ('game', 'plural_name'), ('game', 'player_number'))", 'object_name': 'Race'},
            'game': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'races'", 'to': u"orm['starsweb.Game']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'player_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'plural_name': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
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
        u'starsweb.turn': {
            'Meta': {'ordering': "('-generated',)", 'object_name': 'Turn'},
            'game': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'turns'", 'to': u"orm['starsweb.Game']"}),
            'generated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['starsweb']