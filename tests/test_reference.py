from collections import OrderedDict

from bson import DBRef
from django.test import TestCase
from mongoengine import Document, fields
from rest_framework.fields import IntegerField
from rest_framework.serializers import Serializer

from rest_framework_mongoengine.fields import (
    ComboReferenceField, GenericReferenceField, ReferenceField
)
from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class ReferencedDoc(Document):
    name = fields.StringField()


class ReferencedDocWithUniqueField(Document):
    name = fields.StringField(unique=True)


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


class RefFieldsDoc(Document):
    ref = fields.ReferenceField(ReferencedDoc)
    dbref = fields.ReferenceField(ReferencedDoc, dbref=True)
    cached = fields.CachedReferenceField(ReferencedDoc)
    generic = fields.GenericReferenceField()
    ref_list = fields.ListField(fields.ReferenceField(ReferencedDoc))


class ReferencingDoc(Document):
    ref = fields.ReferenceField(ReferencedDoc)


class ReferencingDocWithUniqueField(Document):
    ref = fields.ReferenceField(ReferencedDocWithUniqueField, unique=True)


class ReferencingDocWithUniqueWithField(Document):
    ref1 = fields.ReferenceField(ReferencedDoc)
    ref2 = fields.ReferenceField(OtherReferencedDoc)

    meta = {
        'indexes': [
            {
                'fields': ['ref1', 'ref2'],
                'unique': True
            }
        ]
    }


class GenericReferencingDoc(Document):
    ref = fields.GenericReferenceField()


class ReferencedSerializer(DocumentSerializer):
    class Meta:
        model = ReferencedDoc
        fields = '__all__'


class ListReferencingModel(Document):
    refs = fields.ListField(ReferenceField(ReferencedDoc))


class RecursiveReferencingDoc(Document):
    ref = fields.ReferenceField('self')


class CustomPkModel(Document):
    name = fields.StringField(primary_key=True)


class ReferencingWithCustomPk(Document):
    ref = fields.ReferenceField(CustomPkModel)


class ReferencingWithCustomPkSerializer(DocumentSerializer):
    class Meta:
        model = ReferencingWithCustomPk
        fields = '__all__'


class ListReferencingWithCustomPk(Document):
    refs = fields.ListField(fields.ReferenceField(CustomPkModel))


class ListReferencingWithCustomPkSerializer(DocumentSerializer):
    class Meta:
        model = ListReferencingWithCustomPk
        fields = '__all__'


class TestReferenceField(TestCase):
    def doCleanups(self):
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
    def doCleanups(self):
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
    def doCleanups(self):
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
        assert isinstance(value, ReferencedDoc)
        assert value.name == "Foo"
        assert value.id is None

    def test_output(self):
        field = ComboReferenceField(serializer=ReferencedSerializer)
        instance = ReferencedDoc.objects.create(name="foo")
        strid = str(instance.id)
        ref = instance.to_dbref()
        assert field.to_representation(instance) == strid
        assert field.to_representation(ref) == strid


class TestReferenceMapping(TestCase):
    maxDiff = 1000

    def test_references(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RefFieldsDoc
                fields = '__all__'

        # order is broken
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref_list = ListField(child=ReferenceField(queryset=ReferencedDoc.objects, required=False), required=False)
                ref = ReferenceField(queryset=ReferencedDoc.objects, required=False)
                dbref = ReferenceField(queryset=ReferencedDoc.objects, required=False)
                cached = ReferenceField(queryset=ReferencedDoc.objects, required=False)
                generic = GenericReferenceField(required=False)
        """)
        assert repr(TestSerializer()) == expected

    def test_shallow(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                fields = '__all__'
                depth = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = ReferenceField(queryset=ReferencedDoc.objects, required=False)
        """)
        assert repr(TestSerializer()) == expected

    def test_deep(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                fields = '__all__'
                depth = 1

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    name = CharField(required=False)
        """)
        assert repr(TestSerializer()) == expected

    def test_recursive(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveReferencingDoc
                fields = '__all__'
                depth = 3

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    ref = NestedSerializer(read_only=True):
                        id = ObjectIdField(read_only=True)
                        ref = NestedSerializer(read_only=True):
                            id = ObjectIdField(read_only=True)
                            ref = ReferenceField(queryset=RecursiveReferencingDoc.objects, required=False)
        """)
        assert repr(TestSerializer()) == expected

    def test_custom_field(self):
        class CustomReferencing(ReferenceField):
            pass

        class TestSerializer(DocumentSerializer):
            serializer_reference_field = CustomReferencing

            class Meta:
                model = ReferencingDoc
                fields = '__all__'
                depth = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = ReferenceField(queryset=ReferencedDoc.objects, required=False)
        """)
        assert repr(TestSerializer()) == expected

    def test_custom_generic(self):
        class CustomReferencing(GenericReferenceField):
            pass

        class TestSerializer(DocumentSerializer):
            serializer_reference_generic = CustomReferencing

            class Meta:
                model = GenericReferencingDoc
                fields = '__all__'
                depth = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = CustomReferencing(required=False)
        """)
        assert repr(TestSerializer()) == expected

    def test_custom_nested(self):
        class CustomReferencing(Serializer):
            foo = IntegerField()

        class TestSerializer(DocumentSerializer):
            serializer_reference_nested = CustomReferencing

            class Meta:
                model = ReferencingDoc
                fields = '__all__'
                depth = 1

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = NestedSerializer(read_only=True):
                    foo = IntegerField()
        """)
        assert repr(TestSerializer()) == expected


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

    def doCleanups(self):
        DisplayableReferencedModel.drop_collection()

    def test_default_display_value(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = DisplayableReferencingModel
                fields = '__all__'

        serializer = TestSerializer()
        expected = OrderedDict([(self.ids[0], 'Red Color'),
                                (self.ids[1], 'Green Color'),
                                (self.ids[2], 'Blue Color')])
        assert serializer.fields['color'].choices == expected

    def test_custom_display_value(self):
        class TestField(ReferenceField):
            def display_value(self, instance):
                return 'My %s Color' % (instance.name)

        class TestSerializer(DocumentSerializer):
            color = TestField(queryset=DisplayableReferencedModel.objects.all())

            class Meta:
                model = DisplayableReferencingModel
                fields = '__all__'

        serializer = TestSerializer()
        expected = OrderedDict([(self.ids[0], 'My Red Color'),
                                (self.ids[1], 'My Green Color'),
                                (self.ids[2], 'My Blue Color')])
        assert serializer.fields['color'].choices == expected


class TestReferenceIntegration(TestCase):
    def setUp(self):
        self.target = ReferencedDoc.objects.create(
            name='Foo'
        )

    def doCleanups(self):
        ReferencedDoc.drop_collection()
        ReferencingDoc.drop_collection()

    def test_retrieval(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                fields = '__all__'
                depth = 0

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': str(self.target.id),
        }
        assert serializer.data == expected

    def test_retrieval_deep(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                fields = '__all__'
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'id': str(self.target.id), 'name': "Foo"}
        }
        assert serializer.data == expected

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                fields = '__all__'

        new_target = ReferencedDoc.objects.create(name="Bar")
        data = {'ref': new_target.id}

        serializer = TestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        assert serializer.data == expected

    def test_update(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                fields = '__all__'

        new_target = ReferencedDoc.objects.create(
            name="Bar"
        )
        data = {
            'ref': new_target.id
        }

        # Serializer should validate okay.
        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.ref.id == new_target.id

        # Representation should be correct.
        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        assert serializer.data == expected


class TestUniqueReferenceIntegration(TestCase):
    def setUp(self):
        self.target = ReferencedDocWithUniqueField.objects.create(
            name='Foo'
        )

    def doCleanups(self):
        ReferencedDocWithUniqueField.drop_collection()
        ReferencingDocWithUniqueField.drop_collection()

    def test_retrieval(self):
        instance = ReferencingDocWithUniqueField.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDocWithUniqueField
                fields = '__all__'
                depth = 0

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': str(self.target.id),
        }
        assert serializer.data == expected

    def test_retrieval_deep(self):
        instance = ReferencingDocWithUniqueField.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDocWithUniqueField
                fields = '__all__'
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'id': str(self.target.id), 'name': "Foo"}
        }
        assert serializer.data == expected

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDocWithUniqueField
                fields = '__all__'

        new_target = ReferencedDocWithUniqueField.objects.create(name="Bar")
        data = {'ref': new_target.id}

        serializer = TestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        assert serializer.data == expected

    def test_update(self):
        instance = ReferencingDocWithUniqueField.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDocWithUniqueField
                fields = '__all__'

        new_target = ReferencedDocWithUniqueField.objects.create(
            name="Bar"
        )
        data = {
            'ref': new_target.id
        }

        # Serializer should validate okay.
        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.ref.id == new_target.id

        # Representation should be correct.
        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        assert serializer.data == expected


class TestUniqueWithReferenceIntegration(TestCase):
    def setUp(self):
        self.target1 = ReferencedDoc.objects.create(
            name='Foo'
        )
        self.target2 = OtherReferencedDoc.objects.create(
            name='Bar'
        )
        self.target2_ = OtherReferencedDoc.objects.create(
            name='Bar2'
        )

    def doCleanups(self):
        ReferencedDocWithUniqueField.drop_collection()
        ReferencingDocWithUniqueWithField.drop_collection()

    def test_retrieval(self):
        instance = ReferencingDocWithUniqueWithField.objects.create(
            ref1=self.target1,
            ref2=self.target2
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDocWithUniqueWithField
                fields = '__all__'
                depth = 0

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref1': str(self.target1.id),
            'ref2': str(self.target2.id),
        }
        assert serializer.data == expected
    
    def test_create(self):
        instance = ReferencingDocWithUniqueWithField.objects.create(
            ref1=self.target1,
            ref2=self.target2
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDocWithUniqueWithField
                fields = '__all__'
                depth = 0

        data = {'ref1': str(self.target1.id), 'ref2': str(self.target2.id)}
        serializer = TestSerializer(data=data)
        assert not serializer.is_valid(), not serializer.errors

        data = {'ref1': str(self.target1.id), 'ref2': str(self.target2_.id)}
        serializer = TestSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        expected = {
            'ref1': str(self.target1.id),
            'ref2': str(self.target2_.id),
        }
        assert serializer.data == expected


    def test_update(self):
        instance1 = ReferencingDocWithUniqueWithField.objects.create(
            ref1=self.target1,
            ref2=self.target2
        )
        instance2 = ReferencingDocWithUniqueWithField.objects.create(
            ref1=self.target1,
            ref2=self.target2_
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDocWithUniqueWithField
                fields = '__all__'
                depth = 0

        data = {'ref1': str(instance1.ref1.id)}
        serializer = TestSerializer(instance1, data=data, partial=True,)
        assert serializer.is_valid(), serializer.errors

        obj = serializer.save()
        assert obj.id == instance1.id
        assert obj.ref1 == instance1.ref1
        assert obj.ref2 == instance1.ref2

        data = {'ref2': str(instance2.ref2.id)}
        serializer = TestSerializer(instance1, data=data, partial=True,)
        assert not serializer.is_valid(), not serializer.errors


class TestGenericReferenceIntegration(TestCase):
    def setUp(self):
        self.target = ReferencedDoc.objects.create(name='Foo')

    def doCleanups(self):
        ReferencedDoc.drop_collection()
        GenericReferencingDoc.drop_collection()

    def test_retrieval(self):
        instance = GenericReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingDoc
                fields = '__all__'
                depth = 0

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedDoc', '_id': str(self.target.id)},
        }
        assert serializer.data == expected

    def test_retrieval_deep(self):
        instance = GenericReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingDoc
                fields = '__all__'
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedDoc', '_id': str(self.target.id)},
        }
        assert serializer.data == expected

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingDoc
                fields = '__all__'

        new_target = ReferencedDoc.objects.create(
            name="Bar"
        )
        data = {
            'ref': {'_cls': 'ReferencedDoc', '_id': new_target.id}
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.ref == new_target.to_dbref()

        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'ReferencedDoc', '_id': str(new_target.id)}
        }
        assert serializer.data == expected

    def test_update(self):
        instance = GenericReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericReferencingDoc
                fields = '__all__'

        new_target = OtherReferencedDoc.objects.create(name="Bar")
        data = {
            'ref': {'_cls': 'OtherReferencedDoc', '_id': new_target.id}
        }

        # Serializer should validate okay.
        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.ref == new_target.to_dbref()

        # Representation should be correct.
        expected = {
            'id': str(instance.id),
            'ref': {'_cls': 'OtherReferencedDoc', '_id': str(new_target.id)}
        }
        assert serializer.data == expected


class ComboReferencingSerializer(DocumentSerializer):
    class Meta:
        model = ReferencingDoc
        fields = '__all__'

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

    def doCleanups(self):
        ReferencedDoc.drop_collection()
        ReferencingDoc.drop_collection()

    def test_retrieval(self):
        instance = ReferencingDoc.objects.create(ref=self.target)
        serializer = ComboReferencingSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': str(self.target.id),
        }
        assert serializer.data == expected

    def test_retrieval_deep(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ReferencingDoc
                fields = '__all__'
                depth = 1

            ref = ComboReferenceField(serializer=ReferencedSerializer)

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'ref': {'id': str(self.target.id), 'name': "Foo"}
        }
        assert serializer.data == expected

    def test_create_ref(self):
        new_target = ReferencedDoc.objects.create(name="Bar")
        data = {'ref': new_target.id}

        serializer = ComboReferencingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        assert serializer.data == expected

    def test_create_data(self):
        data = {'ref': {'name': "Bar"}}

        serializer = ComboReferencingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()

        new_target = ReferencedDoc.objects.get(name="Bar")

        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        assert serializer.data == expected

    def test_update_ref(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        new_target = ReferencedDoc.objects.create(name="Bar")
        data = {'ref': new_target.id}

        serializer = ComboReferencingSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        assert serializer.data == expected

    def test_update_data(self):
        instance = ReferencingDoc.objects.create(ref=self.target)

        data = {'ref': {'name': "Bar"}}

        serializer = ComboReferencingSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()

        new_target = ReferencedDoc.objects.get(name="Bar")

        assert instance.ref.id == new_target.id

        expected = {
            'id': str(instance.id),
            'ref': str(new_target.id)
        }
        assert serializer.data == expected


class TestReferenceCustomPk(TestCase):
    """Operational test

    Test if all operations performed correctly
    """

    def doCleanups(self):
        CustomPkModel.drop_collection()
        ReferencingWithCustomPk.drop_collection()

    def test_parsing(self):
        input_data = {'ref': 'foo'}

        serializer = ReferencingWithCustomPkSerializer(data=input_data)
        # No CustomPkModel object with name 'foo'
        assert not serializer.is_valid(), not serializer.errors

        CustomPkModel.objects.create(name='foo')
        serializer = ReferencingWithCustomPkSerializer(data=input_data)

        assert serializer.is_valid(), serializer.errors

        expected = {'ref': DBRef('custom_pk_model', 'foo')}

        assert serializer.validated_data == expected

    def test_retrieve(self):
        referenced = CustomPkModel.objects.create(name='foo')
        referencing = ReferencingWithCustomPk.objects.create(ref=referenced)
        serializer = ReferencingWithCustomPkSerializer(referencing)

        expected = {
            'id': str(referencing.id),
            'ref': referenced.name
        }

        assert serializer.data == expected

    def test_create(self):
        CustomPkModel.objects.create(name='foo')

        input_data = {'ref': 'unexisting'}
        serializer = ReferencingWithCustomPkSerializer(data=input_data)
        assert not serializer.is_valid(), not serializer.errors

        input_data = {'ref': 'foo'}
        serializer = ReferencingWithCustomPkSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.ref.name == 'foo'

        expected = {
            'id': str(instance.id),
            'ref': 'foo',
        }

        assert serializer.data == expected

    def test_update(self):
        referenced = CustomPkModel.objects.create(name='foo')
        CustomPkModel.objects.create(name='bar')
        instance = ReferencingWithCustomPk.objects.create(ref=referenced)

        data = {'ref': 'unexisting'}
        serializer = ReferencingWithCustomPkSerializer(instance, data=data)
        assert not serializer.is_valid(), not serializer.errors

        data = {'ref': 'bar'}
        serializer = ReferencingWithCustomPkSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.ref.name == 'bar'

        expected = {
            'id': str(instance.id),
            'ref': 'bar',
        }

        assert serializer.data == expected


class TestListReferenceCustomPk(TestCase):
    """Operational test

    Test if all operations performed correctly
    """

    def doCleanups(self):
        CustomPkModel.drop_collection()
        ListReferencingWithCustomPk.drop_collection()

    def test_parsing(self):
        input_data = {'refs': ['foo', 'bar']}

        serializer = ListReferencingWithCustomPkSerializer(data=input_data)
        # No CustomPkModel object with name 'foo'
        assert not serializer.is_valid(), not serializer.errors

        CustomPkModel.objects.create(name='foo')

        serializer = ListReferencingWithCustomPkSerializer(data=input_data)
        # No CustomPkModel object with name 'bar'
        assert not serializer.is_valid(), not serializer.errors

        CustomPkModel.objects.create(name='bar')

        serializer = ListReferencingWithCustomPkSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        expected = {'refs': [
            DBRef('custom_pk_model', 'foo'),
            DBRef('custom_pk_model', 'bar')
        ]}

        assert serializer.validated_data == expected

    def test_retrieve(self):
        referenced = CustomPkModel.objects.create(name='foo')
        referenced2 = CustomPkModel.objects.create(name='bar')
        referencing = ListReferencingWithCustomPk.objects.create(refs=[referenced, referenced2])
        serializer = ListReferencingWithCustomPkSerializer(referencing)

        expected = {
            'id': str(referencing.id),
            'refs': ['foo', 'bar']
        }

        assert serializer.data == expected

    def test_create(self):
        input_data = {'refs': ['foo', 'bar']}
        serializer = ListReferencingWithCustomPkSerializer(data=input_data)
        assert not serializer.is_valid(), not serializer.errors

        CustomPkModel.objects.create(name='foo')

        input_data = {'refs': ['foo', 'bar']}
        serializer = ListReferencingWithCustomPkSerializer(data=input_data)
        assert not serializer.is_valid(), not serializer.errors

        CustomPkModel.objects.create(name='bar')

        input_data = {'refs': ['foo', 'bar']}
        serializer = ListReferencingWithCustomPkSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.refs[0].name == 'foo', instance.refs[1].name == 'bar'

        expected = {
            'id': str(instance.id),
            'refs': ['foo', 'bar'],
        }

        assert serializer.data == expected

    def test_update(self):
        referenced = CustomPkModel.objects.create(name='foo')
        CustomPkModel.objects.create(name='bar')
        instance = ListReferencingWithCustomPk.objects.create(refs=[referenced])

        data = {'refs': ['unexisting']}
        serializer = ListReferencingWithCustomPkSerializer(instance, data=data)
        assert not serializer.is_valid(), not serializer.errors

        data = {'refs': ['bar']}
        serializer = ListReferencingWithCustomPkSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.refs[0].name == 'bar'

        expected = {
            'id': str(instance.id),
            'refs': ['bar'],
        }

        assert serializer.data == expected
