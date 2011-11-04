# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Result'
        db.create_table('ranking_result', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('score', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('ranking', ['Result'])

        # Adding model 'SingleMatch'
        db.create_table('ranking_singlematch', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('winner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='winner', to=orm['accounts.PlayerProfile'])),
            ('loser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='loser', to=orm['accounts.PlayerProfile'])),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ranking.Result'], unique=True)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.City'], null=True, blank=True)),
            ('is_challenged', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('ranking', ['SingleMatch'])

        # Adding model 'Ranking'
        db.create_table('ranking_ranking', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('player', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PlayerProfile'], unique=True)),
            ('points', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('ranking', ['Ranking'])


    def backwards(self, orm):
        
        # Deleting model 'Result'
        db.delete_table('ranking_result')

        # Deleting model 'SingleMatch'
        db.delete_table('ranking_singlematch')

        # Deleting model 'Ranking'
        db.delete_table('ranking_ranking')


    models = {
        'accounts.playerprofile': {
            'Meta': {'object_name': 'PlayerProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'default': "'B'", 'max_length': '1'}),
            'male': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'right_handed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.city': {
            'Meta': {'object_name': 'City'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ranking.ranking': {
            'Meta': {'object_name': 'Ranking'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PlayerProfile']", 'unique': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'ranking.result': {
            'Meta': {'object_name': 'Result'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        'ranking.singlematch': {
            'Meta': {'object_name': 'SingleMatch'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_challenged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'loser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'loser'", 'to': "orm['accounts.PlayerProfile']"}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ranking.Result']", 'unique': 'True'}),
            'winner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'winner'", 'to': "orm['accounts.PlayerProfile']"})
        }
    }

    complete_apps = ['ranking']
