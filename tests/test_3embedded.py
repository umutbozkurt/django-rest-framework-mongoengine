import pytest

from django.test import TestCase

from mongoengine import Document, EmbeddedDocument, fields

from rest_framework.compat import unicode_repr
from rest_framework_mongoengine.serializers import DocumentSerializer, EmbeddedDocumentSerializer

from .utils import dedent, BadType, FieldValues


class EmbeddedModel(EmbeddedDocument):
    foo = fields.StringField()
    bar = fields.StringField()

class EmbeddingModel(Document):
    embedded = fields.EmbeddedDocumentField(EmbeddedModel)
    # generic_embedded_field = fields.GenericEmbeddedDocumentField()

class ListEmbeddingModel(Document):
    embedded_list = fields.EmbeddedDocumentListField(EmbeddedModel)

class NestedEmbeddedModel(EmbeddedDocument):
    embedded = fields.EmbeddedDocumentField(EmbeddedModel)

class NestedEmbeddingModel(Document):
    embedded = fields.EmbeddedDocumentField(NestedEmbeddedModel)

class SelfEmbeddedModel(EmbeddedDocument):
    foo = fields.StringField()
    embedded = fields.EmbeddedDocumentField('self')

class RecursiveEmbeddingModel(Document):
    embedded = fields.EmbeddedDocumentField(SelfEmbeddedModel)


class TestEmbeddedMapping(TestCase):
    def test_embedded_serializer(self):
        class TestSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = EmbeddedModel
        expected = dedent("""
            TestSerializer():
                foo = CharField(required=False)
                bar = CharField(required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_mapping(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedEmbSerializer():
                    foo = CharField(required=False)
                    bar = CharField(required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_mapping_list(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ListEmbeddingModel
                depth = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded_list = NestedEmbSerializer(many=True, required=False):
                    foo = CharField(required=False)
                    bar = CharField(required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_mapping_nodepth(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 0
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = DocumentField(depth=0, model_field=<mongoengine.fields.EmbeddedDocumentField: embedded>, read_only=True)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_mapping_nested(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingModel
                depth = 2
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedEmbSerializer():
                    embedded = NestedEmbSerializer():
                        foo = CharField(required=False)
                        bar = CharField(required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_mapping_nested_nodepth(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingModel
                depth = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedEmbSerializer():
                    embedded = DocumentField(depth=0, model_field=<mongoengine.fields.EmbeddedDocumentField: embedded>, read_only=True)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_mapping_recursive(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveEmbeddingModel
                depth = 3
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedEmbSerializer():
                    foo = CharField(required=False)
                    embedded = NestedEmbSerializer():
                        foo = CharField(required=False)
                        embedded = NestedEmbSerializer():
                            foo = CharField(required=False)
                            embedded = DocumentField(depth=0, model_field=<mongoengine.fields.EmbeddedDocumentField: embedded>, read_only=True)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)


class TestEmbeddedIntegration(TestCase):
    def tearDown(self):
        EmbeddingModel.drop_collection()

    def test_retrival(self):
        instance = EmbeddingModel.objects.create(
            embedded=EmbeddedModel(foo="Foo")
        )
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'embedded': { 'foo': "Foo", 'bar': None },
        }
        self.assertEqual(serializer.data, expected)

    def test_retrival_recursive(self):
        instance = RecursiveEmbeddingModel.objects.create(
            embedded=SelfEmbeddedModel(foo="Foo1", embedded=SelfEmbeddedModel(foo="Foo2", embedded=SelfEmbeddedModel(foo="Foo3")))
        )
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveEmbeddingModel
                depth = 3

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'embedded': { 'foo': "Foo1",
                          'embedded': { 'foo': "Foo2",
                                        'embedded':{ 'foo': "Foo3",
                                                     'embedded': None
                                                     }
                                        }
                          }
        }
        self.assertEqual(serializer.data, expected)

    def test_retrival_recursive_nodepth(self):
        instance = RecursiveEmbeddingModel.objects.create(
            embedded=SelfEmbeddedModel(foo="Foo1", embedded=SelfEmbeddedModel(foo="Foo2", embedded=SelfEmbeddedModel(foo="Foo3")))
        )
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveEmbeddingModel
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'embedded': { 'foo': "Foo1",
                          'embedded': "<tests.test_3embedded.SelfEmbeddedModel>"
                          }
        }
        self.assertEqual(serializer.data, expected)

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 1

        data = {
            'embedded': { 'foo': "Foo" }
        }

        # Serializer should validate okay.
        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.embedded.foo == "Foo"

        # Representation should be correct.
        expected = {
            'id': str(instance.id),
            'embedded': { 'foo': "Foo", 'bar': None}
        }
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = EmbeddingModel.objects.create(
            embedded=EmbeddedModel(foo="Foo", bar="Bar")
        )
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 1

        data = {
            'embedded': { 'bar': "Baz" }
        }
        # Serializer should validate okay.
        serializer = TestSerializer(instance, data=data)

        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.embedded.foo == "Foo"
        assert instance.embedded.bar == "Baz"

        # Representation should be correct.
        expected = {
            'id': str(instance.id),
            'embedded': { 'foo': "Foo", 'bar': "Baz"}
        }
        self.assertEqual(serializer.data, expected)


class ValidatingEmbeddedModel(EmbeddedDocument):
    text = fields.StringField(min_length=3)

class ValidatingEmbeddingModel(Document):
    embedded = fields.EmbeddedDocumentField(ValidatingEmbeddedModel)

class ValidatingSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingEmbeddingModel
        depth = 1

class ValidatingListEmbeddingModel(Document):
    embedded_list = fields.EmbeddedDocumentListField(ValidatingEmbeddedModel)

class ValidatingListSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingListEmbeddingModel
        depth = 1

class TestEmbeddedValidation(TestCase):
    def test_validation_failing(self):
        serializer = ValidatingSerializer(data={'embedded':{'text': 'Fo'}})
        self.assertFalse(serializer.is_valid())
        self.assertIn('embedded', serializer.errors)
        self.assertIn('text', serializer.errors['embedded'])

    def test_validation_passing(self):
        serializer = ValidatingSerializer(data={'embedded':{'text': 'Text'}})
        self.assertTrue(serializer.is_valid())

    def test_list_validation_failing(self):
        serializer = ValidatingListSerializer(data={'embedded_list':[{'text': 'Fo'}]})
        self.assertFalse(serializer.is_valid())
        self.assertIn('embedded_list', serializer.errors)
        self.assertIn('text', serializer.errors['embedded_list'])

    def test_list_validation_passing(self):
        serializer = ValidatingListSerializer(data={'embedded_list':[{'text': 'Text'}]})
        self.assertTrue(serializer.is_valid())
