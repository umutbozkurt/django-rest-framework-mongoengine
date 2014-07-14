from datetime import datetime 
import mongoengine as me 
from unittest import TestCase
from bson import objectid

from rest_framework_mongoengine.serializers import MongoEngineModelSerializer
from rest_framework import serializers as s


class Job(me.Document):
    title = me.StringField()
    status = me.StringField(choices=('draft', 'published'))
    notes = me.StringField(required=False)
    on = me.DateTimeField(default=datetime.utcnow)


class JobSerializer(MongoEngineModelSerializer):
    id = s.Field()
    title = s.CharField()
    status = s.ChoiceField(read_only=True)


    class Meta:
        model = Job 
        fields = ('id', 'title','status')



class TestReadonlyRestore(TestCase):

    def test_restore_object(self):
        job = Job(title='original title', status='draft', notes='secure')
        data = {
            'title': 'updated title ...',
            'status': 'published',  # this one is read only
            'notes': 'hacked' # this field should not update
        }

        serializer = JobSerializer(job, data=data, partial=True)

        self.assertTrue(serializer.is_valid())
        obj = serializer.object 
        self.assertEqual(data['title'], obj.title)
        self.assertEqual('draft', obj.status)
        self.assertEqual('secure', obj.notes)
