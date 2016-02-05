from django.test import TestCase
from mongoengine import Document, EmbeddedDocument, fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import (DocumentSerializer,
                                                    EmbeddedDocumentSerializer)

from .utils import dedent


class EmbeddedModel(EmbeddedDocument):
    foo = fields.StringField()
    bar = fields.StringField()


class EmbeddingModel(Document):
    embedded = fields.EmbeddedDocumentField(EmbeddedModel)


class EmbeddingModel2(Document):
    embedded = fields.EmbeddedDocumentField(EmbeddedModel, required=True)


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


class GenericEmbeddingModel(Document):
    embedded = fields.GenericEmbeddedDocumentField()


class TestEmbeddedMapping(TestCase):
    def test_embdoc(self):
        class TestSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = EmbeddedModel
        expected = dedent("""
            TestSerializer():
                foo = CharField(required=False)
                bar = CharField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedded(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedSerializer(required=False):
                    foo = CharField(required=False)
                    bar = CharField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedded_required(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel2
                depth = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedSerializer(required=True):
                    foo = CharField(required=False)
                    bar = CharField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedded_list(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ListEmbeddingModel
                depth = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded_list = NestedSerializer(many=True, required=False):
                    foo = CharField(required=False)
                    bar = CharField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_shallow(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 0
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = HiddenField(default=None)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_nested(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingModel
                depth = 2
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedSerializer(required=False):
                    embedded = NestedSerializer(required=False):
                        foo = CharField(required=False)
                        bar = CharField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_nested_shallow(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingModel
                depth = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedSerializer(required=False):
                    embedded = HiddenField(default=None)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_recursive(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveEmbeddingModel
                depth = 3
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = NestedSerializer(required=False):
                    foo = CharField(required=False)
                    embedded = NestedSerializer(required=False):
                        foo = CharField(required=False)
                        embedded = NestedSerializer(required=False):
                            foo = CharField(required=False)
                            embedded = HiddenField(default=None)
        """)
        assert unicode_repr(TestSerializer()) == expected


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
            'embedded': {'foo': "Foo", 'bar': None},
        }
        assert serializer.data == expected

    def test_gen_retrival(self):
        instance = GenericEmbeddingModel.objects.create(
            embedded=EmbeddedModel(foo="Foo")
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericEmbeddingModel
                depth = 1

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'embedded': {'_cls': 'EmbeddedModel', 'foo': "Foo", 'bar': None}
        }

        assert serializer.data == expected

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
            'embedded': {'foo': "Foo1",
                         'embedded': {'foo': "Foo2",
                                      'embedded': {'foo': "Foo3"}
                                      }
                         }
        }
        assert serializer.data == expected

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
            'embedded': {'foo': "Foo1"}
        }
        assert serializer.data == expected

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 1

        data = {
            'embedded': {'foo': "Foo"}
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
            'embedded': {'foo': "Foo", 'bar': None}
        }
        assert serializer.data == expected

    def test_gen_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericEmbeddingModel
                depth = 1

        data = {
            'embedded': {'_cls': 'EmbeddedModel', 'foo': "Foo"}
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        self.assertIsInstance(instance.embedded, EmbeddedModel)
        assert instance.embedded.foo == "Foo"

        expected = {
            'id': str(instance.id),
            'embedded': {'_cls': 'EmbeddedModel', 'foo': "Foo", 'bar': None}
        }
        assert serializer.data == expected

    def test_update(self):
        instance = EmbeddingModel.objects.create(
            embedded=EmbeddedModel(foo="Foo", bar="Bar")
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = EmbeddingModel
                depth = 1

        data = {
            'embedded': {'bar': "Baz"}
        }
        serializer = TestSerializer(instance, data=data)

        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.embedded.foo is None
        assert instance.embedded.bar == "Baz"

        expected = {
            'id': str(instance.id),
            'embedded': {'foo': None, 'bar': "Baz"}
        }
        assert serializer.data == expected

    def test_gen_update(self):
        instance = GenericEmbeddingModel.objects.create(
            embedded=EmbeddedModel(foo="Foo", bar="Bar")
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericEmbeddingModel
                depth = 1

        data = {
            'embedded': {'_cls': 'EmbeddedModel', 'bar': "Baz"}
        }
        serializer = TestSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        assert instance.embedded.foo is None
        assert instance.embedded.bar == "Baz"

        expected = {
            'id': str(instance.id),
            'embedded': {'_cls': 'EmbeddedModel', 'foo': None, 'bar': "Baz"}
        }
        assert serializer.data == expected


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
        serializer = ValidatingSerializer(data={'embedded': {'text': 'Fo'}})
        self.assertFalse(serializer.is_valid())
        self.assertIn('embedded', serializer.errors)
        self.assertIn('text', serializer.errors['embedded'])

    def test_validation_passing(self):
        serializer = ValidatingSerializer(data={'embedded': {'text': 'Text'}})
        self.assertTrue(serializer.is_valid())

    def test_nested_validation_failing(self):
        serializer = ValidatingListSerializer(data={'embedded_list': [{'text': 'Fo'}]})
        self.assertFalse(serializer.is_valid())
        self.assertIn('embedded_list', serializer.errors)
        self.assertIn('text', serializer.errors['embedded_list'])

    def test_nested_validation_passing(self):
        serializer = ValidatingListSerializer(data={'embedded_list': [{'text': 'Text'}]})
        self.assertTrue(serializer.is_valid())
