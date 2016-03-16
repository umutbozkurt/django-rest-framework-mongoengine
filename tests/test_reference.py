from collections import OrderedDict

import pytest

from django.test import TestCase
from mongoengine import Document, fields
from rest_framework.compat import unicode_repr
from rest_framework.fields import IntegerField
from rest_framework.serializers import Serializer

from rest_framework_mongoengine.fields import (ComboReferenceField,
                                               GenericReferenceField,
                                               ReferenceField,
                                               DocumentField)
from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class ReferencedDoc(Document):
    name = fields.StringField()


class IntReferencedDoc(Document):
    id = fields.IntField(primary_key=True)
    name = fields.StringField()


class OtherReferencedDoc(Document):
    _meta = {
        'collection': 'other_colection'
    }
    name = fields.StringField()


class IntReferenceField(ReferenceField):
    pk_field_class = IntegerField


class IntGenericReferenceField(GenericReferenceField):
    pk_field_class = IntegerField


class RefFieldsModel(Document):
    ref = fields.ReferenceField(ReferencedDoc)
    dbref = fields.ReferenceField(ReferencedDoc, dbref=True)
    cached = fields.CachedReferenceField(ReferencedDoc)
    generic = fields.GenericReferenceField()
    ref_list = fields.ListField(fields.ReferenceField(ReferencedDoc))


class ReferencingDoc(Document):
    ref = fields.ReferenceField(ReferencedDoc)


class GenericReferencingDoc(Document):
    ref = fields.GenericReferenceField()


class ReferencedSerializer(DocumentSerializer):
    class Meta:
        model = ReferencedDoc


class ListReferencingModel(Document):
    refs = fields.ListField(ReferenceField(ReferencedDoc))


class TestReferenceField(TestCase):
    def tearDown(self):
        ReferencedDoc.drop_collection()
        IntReferencedDoc.drop_collection()
        OtherReferencedDoc.drop_collection()

    def test_init_with_model(self):
        ReferenceField(ReferencedDoc)

    def test_init_with_queryset(self):
        ReferenceField(queryset=ReferencedDoc.objects.all())

    def test_input(self):
        field = ReferenceField(ReferencedDoc)
        instance = ReferencedDoc.objects.create(name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value(str(instance.id)) == ref
        assert field.to_internal_value({'_id': str(instance.id)}) == ref

    def test_output(self):
        field = ReferenceField(ReferencedDoc)
        instance = ReferencedDoc.objects.create(name="foo")
        strid = str(instance.id)
        ref = instance.to_dbref()
        assert field.to_representation(instance) == strid
        assert field.to_representation(ref) == strid

    def test_input_other(self):
        field = ReferenceField(OtherReferencedDoc)
        instance = OtherReferencedDoc.objects.create(name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value(str(instance.id)) == ref
        assert field.to_internal_value({'_id': str(instance.id)}) == ref

    def test_output_other(self):
        field = ReferenceField(OtherReferencedDoc)
        instance = OtherReferencedDoc.objects.create(name="foo")
        strid = str(instance.id)
        ref = instance.to_dbref()
        assert field.to_representation(instance) == strid
        assert field.to_representation(ref) == strid

    def test_input_int(self):
        field = IntReferenceField(IntReferencedDoc)
        instance = IntReferencedDoc.objects.create(id=1, name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value(instance.id) == ref
        assert field.to_internal_value(str(instance.id)) == ref
        assert field.to_internal_value({'_id': instance.id}) == ref
        assert field.to_internal_value({'_id': str(instance.id)}) == ref

    def test_output_int(self):
        field = IntReferenceField(IntReferencedDoc)
        instance = IntReferencedDoc.objects.create(id=1, name="foo")
        intid = instance.id
        ref = instance.to_dbref()
        assert field.to_representation(instance) == intid
        assert field.to_representation(ref) == intid


class TestGenericReferenceField(TestCase):
    def tearDown(self):
        ReferencedDoc.drop_collection()
        IntReferencedDoc.drop_collection()
        OtherReferencedDoc.drop_collection()

    def test_input(self):
        field = GenericReferenceField()
        instance = ReferencedDoc.objects.create(name="foo")
        ref = instance.to_dbref()
        value = field.to_internal_value({'_cls': 'ReferencedDoc', '_id': str(instance.id)})
        assert value == ref

    def test_output(self):
        field = GenericReferenceField()
        instance = ReferencedDoc.objects.create(name="foo")
        ref = instance.to_dbref()
        strid = str(instance.id)
        assert field.to_representation(instance) == {'_cls': 'ReferencedDoc', '_id': strid}
        assert field.to_representation(ref) == {'_cls': 'ReferencedDoc', '_id': strid}

    def test_input_other(self):
        field = GenericReferenceField()
        instance = OtherReferencedDoc.objects.create(name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value({'_cls': 'OtherReferencedDoc', '_id': str(instance.id)}) == ref

    def test_output_other(self):
        field = GenericReferenceField()
        instance = OtherReferencedDoc.objects.create(name="foo")
        strid = str(instance.id)
        ref = instance.to_dbref()
        assert field.to_representation(instance) == {'_cls': 'OtherReferencedDoc', '_id': strid}
        assert field.to_representation(ref) == {'_cls': 'OtherReferencedDoc', '_id': strid}

    def test_input_int(self):
        field = IntGenericReferenceField()
        instance = IntReferencedDoc.objects.create(id=1, name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value({'_cls': 'IntReferencedDoc', '_id': instance.id}) == ref
        assert field.to_internal_value({'_cls': 'IntReferencedDoc', '_id': str(instance.id)}) == ref

    def test_output_int(self):
        field = IntGenericReferenceField()
        instance = IntReferencedDoc.objects.create(id=1, name="foo")
        ref = instance.to_dbref()
        assert field.to_representation(instance) == {'_cls': 'IntReferencedDoc', '_id': instance.id}
        assert field.to_representation(ref) == {'_cls': 'IntReferencedDoc', '_id': instance.id}


class TestComboReferenceField(TestCase):
    def tearDown(self):
        ReferencedDoc.drop_collection()

    def test_input_ref(self):
        field = ComboReferenceField(serializer=ReferencedSerializer)
        instance = ReferencedDoc.objects.create(name="foo")
        ref = instance.to_dbref()
        assert field.to_internal_value(str(instance.id)) == ref
        assert field.to_internal_value({'_id': str(instance.id)}) == ref

    def test_input_data(self):
        field = ComboReferenceField(serializer=ReferencedSerializer)
        value = field.to_internal_value({'name': "Foo"})
        self.assertIsInstance(value, ReferencedDoc)
        self.assertEqual(value.name, "Foo")
        self.assertIsNone(value.id)

    def test_output(self):
        field = ComboReferenceField(serializer=ReferencedSerializer)
        instance = ReferencedDoc.objects.create(name="foo")
        strid = str(instance.id)
        ref = instance.to_dbref()
        assert field.to_representation(instance) == strid
        assert field.to_representation(ref) == strid


class TestReferenceMapping(TestCase):
    maxDiff = 1000

    def test_referenced(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RefFieldsModel
                depth = 0

        # order is broken
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref_list = ListField(child=ReferenceField(queryset=ReferencedDoc.objects), required=False)
                ref = ReferenceField(queryset=ReferencedDoc.objects)
                dbref = ReferenceField(queryset=ReferencedDoc.objects)
                cached = ReferenceField(queryset=ReferencedDoc.objects)
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
                ref_list = NestedSerializer(many=True, required=False):
                    id = ObjectIdField(read_only=True)
                    name = CharField(required=False)
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

    def test_custom_field(self):

        class CustomReferencing(ReferenceField):
            pass

        class TestSerializer(DocumentSerializer):
            serializer_reference_field = CustomReferencing

            class Meta:
                model = ReferencingDoc
                depth = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = CustomReferencing(queryset=ReferencedDoc.objects)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_custom_generic(self):
        class CustomReferencing(DocumentField):
            pass

        class TestSerializer(DocumentSerializer):
            serializer_reference_generic = CustomReferencing

            class Meta:
                model = GenericReferencingDoc
                depth = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = CustomReferencing(model_field=<mongoengine.fields.GenericReferenceField: ref>, required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_custom_nested(self):
        class CustomReferencing(Serializer):
            foo = IntegerField()

        class TestSerializer(DocumentSerializer):
            serializer_reference_nested = CustomReferencing

            class Meta:
                model = ReferencingDoc
                depth = 1

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = NestedSerializer(read_only=True):
                    foo = IntegerField()
        """)
        assert unicode_repr(TestSerializer()) == expected


class DisplayableReferencedModel(Document):
    name = fields.StringField()

    def __str__(self):
        return '%s Color' % (self.name)


class DisplayableReferencingModel(Document):
    color = fields.ReferenceField(DisplayableReferencedModel)


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
        self.target = ReferencedDoc.objects.create(
            name='Foo'
        )

    def tearDown(self):
        ReferencedDoc.drop_collection()
        ReferencingDoc.drop_collection()

    def test_retrival(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                depth = 0

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': str(self.target.id),
        }
        self.assertEqual(serializer.data, expected)

    def test_retrival_deep(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
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
                model = ReferencingDoc

        new_target = ReferencedDoc.objects.create(name="Bar")
        data = {'ref': new_target.id}

        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc

        new_target = ReferencedDoc.objects.create(
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
        self.target = ReferencedDoc.objects.create(name='Foo')

    def tearDown(self):
        ReferencedDoc.drop_collection()
        GenericReferencingDoc.drop_collection()

    def test_retrival(self):
        instance = GenericReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingDoc
                depth = 0

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedDoc', '_id': str(self.target.id)},
        }
        self.assertEqual(serializer.data, expected)

    def test_retrival_deep(self):
        instance = GenericReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingDoc
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedDoc', '_id': str(self.target.id)},
        }
        self.assertEqual(serializer.data, expected)

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingDoc

        new_target = ReferencedDoc.objects.create(
            name="Bar"
        )
        data = {
            'ref': {'_cls': 'ReferencedDoc', '_id': new_target.id}
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.ref == new_target.to_dbref()

        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedDoc', '_id': str(new_target.id)}
        }
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = GenericReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingDoc

        new_target = OtherReferencedDoc.objects.create(name="Bar")
        data = {
            'ref': {'_cls': 'OtherReferencedDoc', '_id': new_target.id}
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
            'ref': {'_cls': 'OtherReferencedDoc', '_id': str(new_target.id)}
        }
        self.assertEqual(serializer.data, expected)


class ComboReferencingSerializer(DocumentSerializer):
    class Meta:
        model = ReferencingDoc
    ref = ComboReferenceField(serializer=ReferencedSerializer)

    def save_subdocs(self, validated_data):
        doc = validated_data['ref']
        if isinstance(doc, Document):
            doc.save()

    def create(self, validated_data):
        self.save_subdocs(validated_data)
        return super(ComboReferencingSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        self.save_subdocs(validated_data)
        return super(ComboReferencingSerializer, self).update(instance, validated_data)


class TestComboReferenceIntegration(TestCase):
    def setUp(self):
        self.target = ReferencedDoc.objects.create(name='Foo')

    def tearDown(self):
        ReferencedDoc.drop_collection()
        ReferencingDoc.drop_collection()

    def test_retrival(self):
        instance = ReferencingDoc.objects.create(ref=self.target)
        serializer = ComboReferencingSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': str(self.target.id),
        }
        self.assertEqual(serializer.data, expected)

    def test_retrival_deep(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                depth = 1
            ref = ComboReferenceField(serializer=ReferencedSerializer)

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'id': str(self.target.id), 'name': "Foo"}
        }
        self.assertEqual(serializer.data, expected)

    def test_create_ref(self):
        new_target = ReferencedDoc.objects.create(name="Bar")
        data = {'ref': new_target.id}

        serializer = ComboReferencingSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        self.assertEqual(serializer.data, expected)

    def test_create_data(self):
        data = {'ref': {'name': "Bar"}}

        serializer = ComboReferencingSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()

        new_target = ReferencedDoc.objects.get(name="Bar")

        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        self.assertEqual(serializer.data, expected)

    def test_update_ref(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        new_target = ReferencedDoc.objects.create(name="Bar")
        data = {'ref': new_target.id}

        serializer = ComboReferencingSerializer(instance, data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        self.assertEqual(serializer.data, expected)

    def test_update_data(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        data = {'ref': {'name': "Bar"}}

        serializer = ComboReferencingSerializer(instance, data=data)
        assert serializer.is_valid()

        instance = serializer.save()

        new_target = ReferencedDoc.objects.get(name="Bar")

        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        self.assertEqual(serializer.data, expected)
