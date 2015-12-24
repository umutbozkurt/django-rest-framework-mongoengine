from collections import OrderedDict

from django.test import TestCase
from mongoengine import fields as me_fields
from mongoengine import Document
from rest_framework.compat import unicode_repr
from rest_framework.fields import IntegerField

from rest_framework_mongoengine.fields import (GenericReferenceField,
                                               ReferenceField)
from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class ReferencedModel(Document):
    name = me_fields.StringField()


class IntReferencedModel(Document):
    id = me_fields.IntField(primary_key=True)
    name = me_fields.StringField()


class IntReferenceField(ReferenceField):
    pk_field_class = IntegerField


class IntGenericReferenceField(GenericReferenceField):
    pk_field_class = IntegerField


class OtherReferencedModel(Document):
    _meta = {
        'collection': 'other_colection'
    }
    name = me_fields.StringField()


class RefFieldsModel(Document):
    ref = me_fields.ReferenceField(ReferencedModel)
    dbref = me_fields.ReferenceField(ReferencedModel, dbref=True)
    cached = me_fields.CachedReferenceField(ReferencedModel)
    generic = me_fields.GenericReferenceField()


class ReferencingModel(Document):
    ref = me_fields.ReferenceField(ReferencedModel)


class GenericReferencingModel(Document):
    ref = me_fields.GenericReferenceField()


class TestReferenceField(TestCase):
    def tearDown(self):
        ReferencedModel.drop_collection()
        IntReferencedModel.drop_collection()
        OtherReferencedModel.drop_collection()

    def test_init_with_model(self):
        ReferenceField(ReferencedModel)

    def test_init_with_queryset(self):
        ReferenceField(queryset=ReferencedModel.objects.all())

    def test_input(self):
        field = ReferenceField(ReferencedModel)
        instance = ReferencedModel.objects.create(name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value(str(instance.id)) == ref
        assert field.to_internal_value({'_id': str(instance.id)}) == ref

    def test_output(self):
        field = ReferenceField(ReferencedModel)
        instance = ReferencedModel.objects.create(name="foo")
        strid = str(instance.id)
        ref = instance.to_dbref()
        assert field.to_representation(instance) == strid
        assert field.to_representation(ref) == strid

    def test_input_other(self):
        field = ReferenceField(OtherReferencedModel)
        instance = OtherReferencedModel.objects.create(name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value(str(instance.id)) == ref
        assert field.to_internal_value({'_id': str(instance.id)}) == ref

    def test_output_other(self):
        field = ReferenceField(OtherReferencedModel)
        instance = OtherReferencedModel.objects.create(name="foo")
        strid = str(instance.id)
        ref = instance.to_dbref()
        assert field.to_representation(instance) == strid
        assert field.to_representation(ref) == strid

    def test_input_int(self):
        field = IntReferenceField(IntReferencedModel)
        instance = IntReferencedModel.objects.create(id=1, name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value(instance.id) == ref
        assert field.to_internal_value(str(instance.id)) == ref
        assert field.to_internal_value({'_id': instance.id}) == ref
        assert field.to_internal_value({'_id': str(instance.id)}) == ref

    def test_output_int(self):
        field = IntReferenceField(IntReferencedModel)
        instance = IntReferencedModel.objects.create(id=1, name="foo")
        intid = instance.id
        ref = instance.to_dbref()
        assert field.to_representation(instance) == intid
        assert field.to_representation(ref) == intid


class TestGenericReferenceField(TestCase):
    def tearDown(self):
        ReferencedModel.drop_collection()
        IntReferencedModel.drop_collection()
        OtherReferencedModel.drop_collection()

    def test_input(self):
        field = GenericReferenceField()
        instance = ReferencedModel.objects.create(name="foo")
        ref = instance.to_dbref()
        value = field.to_internal_value({'_cls': 'ReferencedModel', '_id': str(instance.id)})
        assert value == ref

    def test_output(self):
        field = GenericReferenceField()
        instance = ReferencedModel.objects.create(name="foo")
        ref = instance.to_dbref()
        strid = str(instance.id)
        assert field.to_representation(instance) == {'_cls': 'ReferencedModel', '_id': strid}
        assert field.to_representation(ref) == {'_cls': 'ReferencedModel', '_id': strid}

    def test_input_other(self):
        field = GenericReferenceField()
        instance = OtherReferencedModel.objects.create(name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value({'_cls': 'OtherReferencedModel', '_id': str(instance.id)}) == ref

    def test_output_other(self):
        field = GenericReferenceField()
        instance = OtherReferencedModel.objects.create(name="foo")
        strid = str(instance.id)
        ref = instance.to_dbref()
        assert field.to_representation(instance) == {'_cls': 'OtherReferencedModel', '_id': strid}
        assert field.to_representation(ref) == {'_cls': 'OtherReferencedModel', '_id': strid}

    def test_input_int(self):
        field = IntGenericReferenceField()
        instance = IntReferencedModel.objects.create(id=1, name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value({'_cls': 'IntReferencedModel', '_id': instance.id}) == ref
        assert field.to_internal_value({'_cls': 'IntReferencedModel', '_id': str(instance.id)}) == ref

    def test_output_int(self):
        field = IntGenericReferenceField()
        instance = IntReferencedModel.objects.create(id=1, name="foo")
        ref = instance.to_dbref()
        assert field.to_representation(instance) == {'_cls': 'IntReferencedModel', '_id': instance.id}
        assert field.to_representation(ref) == {'_cls': 'IntReferencedModel', '_id': instance.id}


class TestReferenceMapping(TestCase):
    maxDiff = 1000

    def test_referenced(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RefFieldsModel
                depth = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = ReferenceField(queryset=ReferencedModel.objects)
                dbref = ReferenceField(queryset=ReferencedModel.objects)
                cached = ReferenceField(queryset=ReferencedModel.objects)
                generic = GenericReferenceField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_deep(self):
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
                generic = GenericReferenceField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected


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


class TestReferenceIntegration(TestCase):
    def setUp(self):
        self.target = ReferencedModel.objects.create(
            name='Foo'
        )

    def tearDown(self):
        ReferencedModel.drop_collection()
        ReferencingModel.drop_collection()

    def test_retrival(self):
        instance = ReferencingModel.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingModel
                depth = 0

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': str(self.target.id),
        }
        self.assertEqual(serializer.data, expected)

    def test_retrival_deep(self):
        instance = ReferencingModel.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingModel
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'id': str(self.target.id), 'name': "Foo"}
        }
        self.assertEqual(serializer.data, expected)

    def test_create(self):
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

    def test_update(self):
        instance = ReferencingModel.objects.create(ref=self.target)

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
        serializer = TestSerializer(instance, data=data)
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


class TestGenericReferenceIntegration(TestCase):
    def setUp(self):
        self.target = ReferencedModel.objects.create(name='Foo')

    def tearDown(self):
        ReferencedModel.drop_collection()
        GenericReferencingModel.drop_collection()

    def test_retrival(self):
        instance = GenericReferencingModel.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingModel
                depth = 0

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedModel', '_id': str(self.target.id)},
        }
        self.assertEqual(serializer.data, expected)

    def test_retrival_deep(self):
        instance = GenericReferencingModel.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingModel
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedModel', '_id': str(self.target.id)},
        }
        self.assertEqual(serializer.data, expected)

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingModel

        new_target = ReferencedModel.objects.create(
            name="Bar"
        )
        data = {
            'ref': {'_cls': 'ReferencedModel', '_id': new_target.id}
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.ref == new_target.to_dbref()

        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedModel', '_id': str(new_target.id)}
        }
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = GenericReferencingModel.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingModel

        new_target = OtherReferencedModel.objects.create(name="Bar")
        data = {
            'ref': {'_cls': 'OtherReferencedModel', '_id': new_target.id}
        }

        # Serializer should validate okay.
        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.ref == new_target.to_dbref()

        # Representation should be correct.
        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'OtherReferencedModel', '_id': str(new_target.id)}
        }
        self.assertEqual(serializer.data, expected)
