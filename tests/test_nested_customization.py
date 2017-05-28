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


class CompoundParentDocument(DocumentSerializer):
    foo = fields.StringField()
    embedded_list = fields.EmbeddedDocumentListField(ChildDocument)
    embedded_map = fields.MapField(fields.EmbeddedDocumentField(ChildDocument))


class TestEmbeddedCustomizationMapping(TestCase):
    def test_fields(self):
        """
        Ensure `fields` is passed to embedded documents.
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
        # TODO: what if parent field is not included, but child field is?
        assert unicode_repr(ParentSerializer()) == expected

    def test_exclude(self):
        """
        Ensure `exclude` is passed to embedded documents.
        """
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
        """
        Ensure `read_only` are passed to embedded documents.
        """
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                read_only = ('foo', 'embedded.name')
                depth = 1

        expected = dedent("""
            ParentSerializer():
                id = ObjectIdField(read_only=True)
                foo = CharField(required=False)
                nested_reference = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    foo = CharField(required=False)
                    bar = CharField(required=False)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    age = IntegerField(required=False)
        """)

        assert unicode_repr(ParentSerializer()) == expected

    def test_extra_field_kwargs(self):
        """
        Ensure `extra_kwargs` are passed to embedded documents.
        """
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


class TestEmbeddedCustomizationIntegration(TestCase):
    def test_fields(self):
        pass

    def test_exclude(self):
        pass

    def test_read_only(self):
        pass

    def test_extra_field_kwargs(self):
        pass
