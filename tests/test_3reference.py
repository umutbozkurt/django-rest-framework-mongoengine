import pytest
from collections import OrderedDict

from django.test import TestCase
from django.utils.encoding import smart_str

from bson import ObjectId, DBRef
from mongoengine import Document, fields as me_fields
from rest_framework.compat import unicode_repr
from rest_framework.test import APISimpleTestCase
from rest_framework.exceptions import ValidationError

from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine.fields import ReferenceField

from .utils import dedent, BadType, FieldValues


class ReferencedModel(Document):
    name = me_fields.StringField()


class RefFieldsModel(Document):
    ref = me_fields.ReferenceField(ReferencedModel)
    dbref = me_fields.ReferenceField(ReferencedModel, dbref=True)
    cached = me_fields.CachedReferenceField(ReferencedModel)
    # gen_ref_field = me_fields.GenericReferenceField()


class ReferencingModel(Document):
    ref = me_fields.ReferenceField(ReferencedModel)


someobjectid = ObjectId('563547d9a21aab31b7e73ac9')
somedbref = DBRef('referenced_model', someobjectid)

class TestReferenceFieldValue(FieldValues, TestCase):
    field = ReferenceField(ReferencedModel)

    @classmethod
    def setUpClass(cls):
        ReferencedModel.objects.create(id=someobjectid)

    @classmethod
    def tearDownClass(cls):
        ReferencedModel.drop_collection()

    valid_inputs = {
        somedbref: somedbref,
        someobjectid: somedbref,
        str(someobjectid): somedbref
    }
    invalid_inputs = {
        123: ['Incorrect type. Expected str|ObjectId|DBRef|Document value, received int.'],
        'xxx': ['"xxx" is not a valid ObjectId']
    }
    outputs = {
        somedbref: str(someobjectid),
        someobjectid: str(someobjectid),
        str(someobjectid): str(someobjectid)
    }


class TestReferenceField(APISimpleTestCase):
    def setUp(self):
        self.objects = [
            ReferencedModel.objects.create(name='foo'),
            ReferencedModel.objects.create(name='bar'),
            ReferencedModel.objects.create(name='baz')
        ]
        self.instance = self.objects[1]

    def tearDown(self):
        ReferencedModel.drop_collection()

    def test_init_with_model(self):
        ReferenceField(ReferencedModel)

    def test_init_with_queryset(self):
        ReferenceField(queryset=ReferencedModel.objects.all())

    def test_pk_related_lookup_exists(self):
        field = ReferenceField(ReferencedModel)
        instance = field.to_internal_value(self.instance.id)
        assert instance == self.instance.to_dbref()

    def test_pk_related_lookup_does_not_exist(self):
        oid = ObjectId()
        field = ReferenceField(ReferencedModel)
        with pytest.raises(ValidationError) as excinfo:
            field.to_internal_value(oid)
        msg = excinfo.value.detail[0]
        assert msg == 'Invalid id "%s" - object does not exist.' % oid

    def test_pk_related_lookup_invalid_type(self):
        field = ReferenceField(ReferencedModel)
        with pytest.raises(ValidationError) as excinfo:
            field.to_internal_value(BadType())
        msg = excinfo.value.detail[0]
        assert msg == 'Incorrect type. Expected str|ObjectId|DBRef|Document value, received BadType.'

    def test_pk_representation(self):
        field = ReferenceField(ReferencedModel)
        representation = field.to_representation(self.instance)
        assert representation == smart_str(self.instance.id)


class TestMapping(TestCase):
    maxDiff = 1000
    def test_pk_relations(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RefFieldsModel
                depth = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = ReferenceField(queryset=ReferencedModel.objects.all())
                dbref = ReferenceField(queryset=ReferencedModel.objects.all())
                cached = ReferenceField(queryset=ReferencedModel.objects.all())
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_nested_relations(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RefFieldsModel
                depth = 1

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    name = CharField(required=False)
                dbref = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    name = CharField(required=False)
                cached = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    name = CharField(required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_nested_unique_together_relations(self):
        pytest.skip("Not yet implemented")


class DisplayableReferencedModel(Document):
    name = me_fields.StringField()

    def __str__(self):
        return '%s Color' % (self.name)


class DisplayableReferencingModel(Document):
    color = me_fields.ReferenceField(DisplayableReferencedModel)


class TestRelationalFieldDisplayValue(TestCase):
    def setUp(self):
        self.objects = [
            DisplayableReferencedModel.objects.create(name='Red'),
            DisplayableReferencedModel.objects.create(name='Green'),
            DisplayableReferencedModel.objects.create(name='Blue')
        ]
        self.ids = list(map(lambda e: str(e.id), self.objects))

    def tearDown(self):
        DisplayableReferencedModel.drop_collection()

    def test_default_display_value(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = DisplayableReferencingModel

        serializer = TestSerializer()
        expected = OrderedDict([(self.ids[0], 'Red Color'),
                                (self.ids[1], 'Green Color'),
                                (self.ids[2], 'Blue Color')])
        self.assertEqual(serializer.fields['color'].choices, expected)

    def test_custom_display_value(self):
        class TestField(ReferenceField):
            def display_value(self, instance):
                return 'My %s Color' % (instance.name)

        class TestSerializer(DocumentSerializer):
            color = TestField(queryset=DisplayableReferencedModel.objects.all())

            class Meta:
                model = DisplayableReferencingModel

        serializer = TestSerializer()
        expected = OrderedDict([(self.ids[0], 'My Red Color'),
                                (self.ids[1], 'My Green Color'),
                                (self.ids[2], 'My Blue Color')])
        self.assertEqual(serializer.fields['color'].choices, expected)


class TestIntegration(TestCase):
    def setUp(self):
        self.target = ReferencedModel.objects.create(
            name='Foo'
        )
        self.instance = ReferencingModel.objects.create(
            ref=self.target,
        )

    def tearDown(self):
        ReferencedModel.drop_collection()
        ReferencingModel.drop_collection()

    def test_pk_retrival(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingModel
                depth = 0

        serializer = TestSerializer(self.instance)
        expected = {
            'id': str(self.instance.id),
            'ref': str(self.target.id),
        }
        self.assertEqual(serializer.data, expected)

    def test_pk_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingModel

        new_target = ReferencedModel.objects.create(
            name="Bar"
        )
        data = {
            'ref': new_target.id
        }

        # Serializer should validate okay.
        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.ref.id == new_target.id

        # Representation should be correct.
        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        self.assertEqual(serializer.data, expected)

    def test_pk_update(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingModel

        new_target = ReferencedModel.objects.create(
            name="Bar"
        )
        data = {
            'ref': new_target.id
        }

        # Serializer should validate okay.
        serializer = TestSerializer(self.instance, data=data)
        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.ref.id == new_target.id

        # Representation should be correct.
        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        self.assertEqual(serializer.data, expected)
