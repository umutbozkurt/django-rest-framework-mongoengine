"""
We want to allow users override fields and their attributes on
auto-generated embedded documents based on

We need to take into account the following fields:
 - exclude
 - read_only
 - extra_kwargs
"""

from __future__ import unicode_literals

from django.test import TestCase
from mongoengine import Document, EmbeddedDocument, fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class ChildDocument(EmbeddedDocument):
    name = fields.StringField()
    age = fields.IntField()


class ReferencedDocument(Document):
    foo = fields.StringField()
    bar = fields.StringField()


class ParentDocument(Document):
    foo = fields.StringField()
    embedded = fields.EmbeddedDocumentField(ChildDocument)
    nested_reference = fields.ReferenceField(ReferencedDocument)


class CompoundParentDocument(Document):
    foo = fields.StringField()
    embedded_list = fields.EmbeddedDocumentListField(ChildDocument)
    list_of_embedded_documents = fields.ListField(fields.EmbeddedDocumentField(ChildDocument))
    embedded_map = fields.MapField(fields.EmbeddedDocumentField(ChildDocument))


class TestEmbeddedCustomizationMapping(TestCase):
    def test_fields(self):
        """
        Ensure `fields` is passed to embedded documents.
        If 'embedded.name' is included, 'embedded' should be included, too.
        """
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('embedded', 'embedded.name', 'nested_reference', 'nested_reference.foo')
                depth = 1

        expected = dedent("""
            ParentSerializer():
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                nested_reference = NestedSerializer(read_only=True):
                    foo = CharField(required=False)
        """)
        assert unicode_repr(ParentSerializer()) == expected

    def test_exclude(self):
        """Ensure `exclude` is passed to embedded documents."""
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                exclude = ('foo', 'embedded.age')
                depth = 1

        expected = dedent("""
            ParentSerializer():
                id = ObjectIdField(read_only=True)
                nested_reference = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    foo = CharField(required=False)
                    bar = CharField(required=False)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
        """)

        assert unicode_repr(ParentSerializer()) == expected

    def test_read_only(self):
        """Ensure `read_only` are passed to embedded documents."""
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                read_only_fields = ('foo', 'embedded.name')
                depth = 1

        expected = dedent("""
            ParentSerializer():
                id = ObjectIdField(read_only=True)
                foo = CharField(read_only=True)
                nested_reference = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    foo = CharField(required=False)
                    bar = CharField(required=False)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(read_only=True)
                    age = IntegerField(required=False)
        """)

        assert unicode_repr(ParentSerializer()) == expected

    def test_extra_field_kwargs(self):
        """Ensure `extra_kwargs` are passed to embedded documents."""
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                depth = 1
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded.name': {'default': 'Johnny B. Good'}
                }

        expected = dedent("""
            ParentSerializer():
                id = ObjectIdField(read_only=True)
                foo = CharField(default='bar')
                nested_reference = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    foo = CharField(required=False)
                    bar = CharField(required=False)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(default='Johnny B. Good')
                    age = IntegerField(required=False)
        """)

        assert unicode_repr(ParentSerializer()) == expected


class TestCompoundCustomizationMapping(TestCase):
    def test_fields(self):
        """Ensure `fields` is passed to embedded documents."""
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = (
                    'embedded_list',
                    'embedded_list.child.name',
                    'embedded_map',
                    'embedded_map.child.age',
                    'list_of_embedded_documents',
                    'list_of_embedded_documents.child.name')
                depth = 1

        expected = dedent("""
            CompoundParentSerializer():
                embedded_list = EmbeddedSerializer(many=True, required=False):
                    name = CharField(required=False)
                embedded_map = DictField(child=EmbeddedSerializer(required=False), required=False):
                    age = IntegerField(required=False)
                list_of_embedded_documents = EmbeddedSerializer(many=True, required=False):
                    name = CharField(required=False)
        """)

        serializer = CompoundParentSerializer()
        unicode_repr(serializer)

        assert unicode_repr(CompoundParentSerializer()) == expected

    def test_exclude(self):
        """Ensure `exclude` is passed to embedded documents."""
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                exclude = (
                    'id',
                    'foo',
                    'embedded_list.child.age',
                    'embedded_map.child.name',
                    'list_of_embedded_documents.child.age'
                )

        expected = dedent("""
            CompoundParentSerializer():
                embedded_list = EmbeddedSerializer(many=True, required=False):
                    name = CharField(required=False)
                list_of_embedded_documents = EmbeddedSerializer(many=True, required=False):
                    name = CharField(required=False)
                embedded_map = DictField(child=EmbeddedSerializer(required=False), required=False):
                    age = IntegerField(required=False)
        """)

        assert unicode_repr(CompoundParentSerializer()) == expected

    def test_read_only(self):
        """Ensure `read_only` are passed to embedded documents."""
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = ('__all__')
                read_only_fields = (
                    'foo',
                    'embedded_list.child.name',
                    'list_of_embedded_documents.child.name',
                    'embedded_map.child.name'
                )

        expected = dedent("""
            CompoundParentSerializer():
                id = ObjectIdField(read_only=True)
                foo = CharField(read_only=True)
                embedded_list = EmbeddedSerializer(many=True, required=False):
                    name = CharField(read_only=True)
                    age = IntegerField(required=False)
                list_of_embedded_documents = EmbeddedSerializer(many=True, required=False):
                    name = CharField(read_only=True)
                    age = IntegerField(required=False)
                embedded_map = DictField(child=EmbeddedSerializer(required=False), required=False):
                    name = CharField(read_only=True)
                    age = IntegerField(required=False)
        """)

        assert unicode_repr(CompoundParentSerializer()) == expected

    def test_extra_field_kwargs(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = ('__all__')
                depth = 1
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded_list.child.name': {'default': 'Johnny'},
                    'list_of_embedded_documents.child.name': {'default': 'B'},
                    'embedded_map.child.name': {'default': 'Good'}
                }

        expected = dedent("""
            CompoundParentSerializer():
                id = ObjectIdField(read_only=True)
                foo = CharField(default='bar')
                embedded_list = EmbeddedSerializer(many=True, required=False):
                    name = CharField(default='Johnny')
                    age = IntegerField(required=False)
                list_of_embedded_documents = EmbeddedSerializer(many=True, required=False):
                    name = CharField(default='B')
                    age = IntegerField(required=False)
                embedded_map = DictField(child=EmbeddedSerializer(required=False), required=False):
                    name = CharField(default='Good')
                    age = IntegerField(required=False)
        """)

        assert unicode_repr(CompoundParentSerializer()) == expected


class TestEmbeddedCustomizationFieldsIntegration(TestCase):
    class ParentSerializer(DocumentSerializer):
        class Meta:
            model = ParentDocument
            fields = ('embedded', 'embedded.name', 'nested_reference', 'nested_reference.foo')
            depth = 1

    def doCleanups(self):
        ParentDocument.drop_collection()

    def test_parsing(self):
        input_data = {
            "foo":  "x",
            "embedded": {'name': 'Joe', 'age': 9},
            "nested_reference": {'foo': 'a', 'bar': 'b'}
        }

        import pdb
        pdb.set_trace()

        serializer = self.ParentSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            u'embedded': {u'name': u'Joe'},
            u'nested_reference': {u'foo': u'a'}
        }

        assert serializer.validated_data == expected

    def test_retrieval(self):
        pass

    def test_create(self):
        pass

    def test_update(self):
        pass

    def test_delete(self):
        pass


class TestEmbeddedCustomizationExcludeIntegration(TestCase):
    class ParentSerializer(DocumentSerializer):
        class Meta:
            model = ParentDocument
            exclude = ('foo', 'embedded.age')
            depth = 1

    def doCleanups(self):
        ParentDocument.drop_collection()

    def test_parsing(self):
        pass

    def test_retrieval(self):
        pass

    def test_create(self):
        pass

    def test_update(self):
        pass

    def test_delete(self):
        pass


class TestEmbeddedCustomizationReadOnlyIntegration(TestCase):
    class ParentSerializer(DocumentSerializer):
        class Meta:
            model = ParentDocument
            fields = ('__all__')
            read_only_fields = ('foo', 'embedded.name')
            depth = 1

    def doCleanups(self):
        ParentDocument.drop_collection()

    def test_parsing(self):
        pass

    def test_retrieval(self):
        pass

    def test_create(self):
        pass

    def test_update(self):
        pass

    def test_delete(self):
        pass


class TestEmbeddedCustomizationExtraFieldKwargsIntegration(TestCase):
    class ParentSerializer(DocumentSerializer):
        class Meta:
            model = ParentDocument
            fields = ('__all__')
            depth = 1
            extra_kwargs = {
                'foo': {'default': 'bar'},
                'embedded.name': {'default': 'Johnny B. Good'}
            }

    def doCleanups(self):
        ParentDocument.drop_collection()

    def test_parsing(self):
        pass

    def test_retrieval(self):
        pass

    def test_create(self):
        pass

    def test_update(self):
        pass

    def test_delete(self):
        pass


class TestEmbeddedCustomizationValidateMethodIntegration(TestCase):
    def doCleanups(self):
        ParentDocument.drop_collection()

    def test_parsing(self):
        pass

    def test_retrieval(self):
        pass

    def test_put(self):
        pass

    def test_post(self):
        pass

    def test_delete(self):
        pass
