# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'CourtSetup'
        db.create_table('clubs_courtsetup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('club', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.ClubProfile'])),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('clubs', ['CourtSetup'])

        # Adding model 'Court'
        db.create_table('clubs_court', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('court_setup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['clubs.CourtSetup'])),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('indoor', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('light', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('surface', self.gf('django.db.models.fields.CharField')(default='CL', max_length=2)),
            ('single_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_available', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('clubs', ['Court'])

        # Adding unique constraint on 'Court', fields ['court_setup', 'number']
        db.create_unique('clubs_court', ['court_setup_id', 'number'])

        # Adding model 'Vacancy'
        db.create_table('clubs_vacancy', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('court', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['clubs.Court'])),
            ('day_of_week', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('available_from', self.gf('django.db.models.fields.IntegerField')(default=8)),
            ('available_to', self.gf('django.db.models.fields.IntegerField')(default=9)),
            ('price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('clubs', ['Vacancy'])

        # Adding unique constraint on 'Vacancy', fields ['court', 'day_of_week', 'available_from', 'available_to']
        db.create_unique('clubs_vacancy', ['court_id', 'day_of_week', 'available_from', 'available_to'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Vacancy', fields ['court', 'day_of_week', 'available_from', 'available_to']
        db.delete_unique('clubs_vacancy', ['court_id', 'day_of_week', 'available_from', 'available_to'])

        # Removing unique constraint on 'Court', fields ['court_setup', 'number']
        db.delete_unique('clubs_court', ['court_setup_id', 'number'])

        # Deleting model 'CourtSetup'
        db.delete_table('clubs_courtsetup')

        # Deleting model 'Court'
        db.delete_table('clubs_court')

        # Deleting model 'Vacancy'
        db.delete_table('clubs_vacancy')


    models = {
        'accounts.clubprofile': {
            'Meta': {'object_name': 'ClubProfile'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']"}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
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
        'clubs.court': {
            'Meta': {'unique_together': "(('court_setup', 'number'),)", 'object_name': 'Court'},
            'court_setup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['clubs.CourtSetup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indoor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'light': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'single_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'surface': ('django.db.models.fields.CharField', [], {'default': "'CL'", 'max_length': '2'})
        },
        'clubs.courtsetup': {
            'Meta': {'object_name': 'CourtSetup'},
            'club': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.ClubProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'clubs.vacancy': {
            'Meta': {'unique_together': "(('court', 'day_of_week', 'available_from', 'available_to'),)", 'object_name': 'Vacancy'},
            'available_from': ('django.db.models.fields.IntegerField', [], {'default': '8'}),
            'available_to': ('django.db.models.fields.IntegerField', [], {'default': '9'}),
            'court': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['clubs.Court']"}),
            'day_of_week': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'})
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
        }
    }

    complete_apps = ['clubs']
