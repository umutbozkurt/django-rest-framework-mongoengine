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
from rest_framework.serializers import ValidationError

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


class TestNestedCustomizationMapping(TestCase):
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


class TestNestedCustomizationFieldsIntegration(TestCase):
    def doCleanups(self):
        ReferencedDocument.drop_collection()
        ParentDocument.drop_collection()

    def test_parsing(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('embedded', 'embedded.name', 'nested_reference', 'nested_reference.foo')
                depth = 1

        input_data = {
            "foo": "x",
            "embedded": {'name': 'Joe', 'age': 9},
            "nested_reference": {'foo': 'a', 'bar': 'b'}
        }

        serializer = ParentSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            u'embedded': {u'name': u'Joe'}
        }

        assert serializer.validated_data == expected

    def test_retrieval(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('embedded', 'embedded.name', 'nested_reference', 'nested_reference.foo')
                depth = 1

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )
        serializer = ParentSerializer(instance)
        expected = {
            'nested_reference': {'foo': 'a'},
            'embedded': {'name': 'Joe'}
        }
        assert serializer.data == expected

    def test_create(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('embedded', 'embedded.name', 'nested_reference')

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        data = {
            'nested_reference': nested_reference.id,
            'embedded': {'name': 'Joe'}
        }

        serializer = ParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Joe'}
        }
        assert serializer.data == expected

    def test_update(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('embedded', 'embedded.name', 'nested_reference')

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )

        data = {
            'embedded': {'name': 'Jack'}
        }

        serializer = ParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Jack'}
        }
        assert serializer.data == expected


class TestNestedCustomizationExcludeIntegration(TestCase):
    def doCleanups(self):
        ReferencedDocument.drop_collection()
        ParentDocument.drop_collection()

    def test_parsing(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                exclude = ('foo', 'embedded.age', 'nested_reference.bar')
                depth = 1

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )
        serializer = ParentSerializer(instance)
        expected = {
            'id': str(instance.id),
            'nested_reference': {'id': str(nested_reference.id), 'foo': 'a'},
            'embedded': {'name': 'Joe'}
        }
        assert serializer.data == expected

    def test_retrieval(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                exclude = ('foo', 'embedded.age', 'nested_reference.bar')
                depth = 1

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )
        serializer = ParentSerializer(instance)
        expected = {
            'id': str(instance.id),
            'nested_reference': {'id': str(nested_reference.id), 'foo': 'a'},
            'embedded': {'name': 'Joe'}
        }
        assert serializer.data == expected

    def test_create(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                exclude = ('foo', 'embedded.age')

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        data = {
            'nested_reference': nested_reference.id,
            'embedded': {'name': 'Joe'}
        }

        serializer = ParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Joe'}
        }
        assert serializer.data == expected

    def test_update(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                exclude = ('foo', 'embedded.age')

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )

        data = {
            'embedded': {'name': 'Jack'}
        }

        serializer = ParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Jack'}
        }
        assert serializer.data == expected


class TestNestedCustomizationReadOnlyIntegration(TestCase):
    def doCleanups(self):
        ReferencedDocument.drop_collection()
        ParentDocument.drop_collection()

    def test_parsing(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                read_only_fields = ('foo', 'embedded.name')
                depth = 1

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )
        serializer = ParentSerializer(instance)
        expected = {
            'id': str(instance.id),
            'foo': 'x',
            'nested_reference': {'id': str(nested_reference.id), 'foo': 'a', 'bar': 'b'},
            'embedded': {'name': 'Joe', 'age': 9}
        }
        assert serializer.data == expected

    def test_retrieval(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                read_only_fields = ('foo', 'embedded.name')
                depth = 1

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )
        serializer = ParentSerializer(instance)
        expected = {
            'id': str(instance.id),
            'foo': 'x',
            'nested_reference': {'id': str(nested_reference.id), 'foo': 'a', 'bar': 'b'},
            'embedded': {'name': 'Joe', 'age': 9}
        }
        assert serializer.data == expected

    def test_create(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                read_only_fields = ('foo', 'embedded.age')

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        data = {
            'foo': 'x',
            'nested_reference': nested_reference.id,
            'embedded': {'name': 'Joe', 'age': 9}
        }

        serializer = ParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'foo': None,
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Joe', 'age': None}
        }
        assert serializer.data == expected

    def test_update(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                read_only_fields = ('foo', 'embedded.age')

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )

        data = {
            'embedded': {'name': 'Jack', 'age': 10}
        }

        serializer = ParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'foo': 'x',
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Jack', 'age': None}
        }
        assert serializer.data == expected


class TestNestedCustomizationExtraFieldKwargsIntegration(TestCase):
    def doCleanups(self):
        ReferencedDocument.drop_collection()
        ParentDocument.drop_collection()

    def test_parsing(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                depth = 1
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded.name': {'default': 'Johnny B. Good'}
                }

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )
        serializer = ParentSerializer(instance)
        expected = {
            'id': str(instance.id),
            'foo': 'x',
            'nested_reference': {'id': str(nested_reference.id), 'foo': 'a', 'bar': 'b'},
            'embedded': {'name': 'Joe', 'age': 9}
        }
        assert serializer.data == expected

    def test_retrieval(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                depth = 1
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded.name': {'default': 'Johnny B. Good'}
                }

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )
        serializer = ParentSerializer(instance)
        expected = {
            'id': str(instance.id),
            'foo': 'x',
            'nested_reference': {'id': str(nested_reference.id), 'foo': 'a', 'bar': 'b'},
            'embedded': {'name': 'Joe', 'age': 9}
        }
        assert serializer.data == expected

    def test_create(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded.name': {'default': 'Johnny B. Good'}
                }

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        data = {
            'nested_reference': nested_reference.id,
            'embedded': {'age': 9}
        }

        serializer = ParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'foo': 'bar',
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Johnny B. Good', 'age': 9}
        }
        assert serializer.data == expected

    def test_update(self):
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded.name': {'default': 'Johnny B. Good'}
                }

        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Joe', age=9),
            nested_reference=nested_reference
        )

        data = {
            'embedded': {'age': 10}
        }

        serializer = ParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'foo': 'bar',
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Johnny B. Good', 'age': 10}
        }
        assert serializer.data == expected


class TestNestedCustomizationValidateMethodIntegration(TestCase):
    class ParentSerializer(DocumentSerializer):
        class Meta:
            model = ParentDocument
            fields = ('__all__')

        def validate_embedded__name(self, value):
            if len(value) < 4:
                raise ValidationError('Minimum 4 characters.')
            return value.title()

    def doCleanups(self):
        ReferencedDocument.drop_collection()
        ParentDocument.drop_collection()

    def test_create_success(self):
        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        data = {
            'foo': 'x',
            'nested_reference': nested_reference.id,
            'embedded': {'name': "Jack", 'age': 9}
        }

        serializer = self.ParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'foo': 'x',
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Jack', 'age': 9}
        }
        assert serializer.data == expected

    def test_create_fail(self):
        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        data = {
            'foo': 'x',
            'nested_reference': nested_reference.id,
            'embedded': {'name': "Joe", 'age': 9}
        }

        serializer = self.ParentSerializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'embedded': {'name': [u'Minimum 4 characters.']}}

    def test_update_success(self):
        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Jack', age=9),
            nested_reference=nested_reference
        )

        data = {
            'embedded': {'name': 'Johnny B. Good'}
        }

        serializer = self.ParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        # TODO: passing empty 'age' resets it to None - is this expected behavior, or we should raise error?
        expected = {
            'id': str(serializer.instance.id),
            'foo': 'x',
            'nested_reference': str(nested_reference.id),
            'embedded': {'name': 'Johnny B. Good', 'age': None}
        }
        assert serializer.data == expected

    def test_update_fail(self):
        nested_reference = ReferencedDocument.objects.create(foo='a', bar='b')
        instance = ParentDocument.objects.create(
            foo='x',
            embedded=ChildDocument(name='Jack', age=9),
            nested_reference=nested_reference
        )

        data = {
            'embedded': {'name': 'Joe'}
        }

        serializer = self.ParentSerializer(instance, data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'embedded': {'name': [u'Minimum 4 characters.']}}


class TestNestedCompoundCustomizationFieldsIntegration(TestCase):
    def doCleanups(self):
        CompoundParentDocument.drop_collection()

    def test_parsing(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = (
                    'embedded_list',
                    'embedded_list.child.name',
                    'embedded_map',
                    'embedded_map.child.age',
                    'list_of_embedded_documents',
                    'list_of_embedded_documents.child.name'
                )
                depth = 1

        input_data = {
            "embedded_list": [{'name': 'Joe'}],
            "embedded_map": {'0': {'age': 9}},
            "list_of_embedded_documents": [{'name': 'Joe'}]
        }

        serializer = CompoundParentSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            "embedded_list": [{'name': 'Joe'}],
            "embedded_map": {'0': {'age': 9}},
            "list_of_embedded_documents": [{'name': 'Joe'}]
        }

        assert serializer.validated_data == expected

    def test_retrieval(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = (
                    'embedded_list',
                    'embedded_list.child.name',
                    'embedded_map',
                    'embedded_map.child.age',
                    'list_of_embedded_documents',
                    'list_of_embedded_documents.child.name'
                )
                depth = 1

        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )
        serializer = CompoundParentSerializer(instance)
        expected = {
            'embedded_list': [{'name': 'Joe'}],
            'embedded_map': {'Joe': {'age': 9}},
            'list_of_embedded_documents': [{'name': 'Joe'}]
        }
        assert serializer.data == expected

    def test_create(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = (
                    'embedded_list',
                    'embedded_list.child.name',
                    'embedded_map',
                    'embedded_map.child.age',
                    'list_of_embedded_documents',
                    'list_of_embedded_documents.child.name'
                )

        data = {
            'embedded_list': [{'name': 'Joe'}],
            'embedded_map': {'Joe': {'age': 9}},
            'list_of_embedded_documents': [{'name': 'Joe'}]
        }

        serializer = CompoundParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'embedded_list': [{'name': 'Joe'}],
            'embedded_map': {'Joe': {'age': 9}},
            'list_of_embedded_documents': [{'name': 'Joe'}]
        }
        assert serializer.data == expected

    def test_update(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = (
                    'embedded_list',
                    'embedded_list.child.name',
                    'embedded_map',
                    'embedded_map.child.age',
                    'list_of_embedded_documents',
                    'list_of_embedded_documents.child.name'
                )

        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )

        data = {
            'embedded_list': [{'name': 'Jack'}],
            'embedded_map': {'Joe': {'age': 10}},
            'list_of_embedded_documents': [{'name': 'Jack'}]
        }

        serializer = CompoundParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'embedded_list': [{'name': 'Jack'}],
            'embedded_map': {'Joe': {'age': 10}},
            'list_of_embedded_documents': [{'name': 'Jack'}]
        }
        assert serializer.data == expected


class TestNestedCompoundCustomizationExcludeIntegration(TestCase):
    def doCleanups(self):
        CompoundParentDocument.drop_collection()

    def test_parsing(self):
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
                depth = 1

        input_data = {
            "embedded_list": [{'name': 'Joe'}],
            "embedded_map": {'0': {'age': 9}},
            "list_of_embedded_documents": [{'name': 'Joe'}]
        }

        serializer = CompoundParentSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            "embedded_list": [{'name': 'Joe'}],
            "embedded_map": {'0': {'age': 9}},
            "list_of_embedded_documents": [{'name': 'Joe'}]
        }

        assert serializer.validated_data == expected

    def test_retrieval(self):
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
                depth = 1

        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )
        serializer = CompoundParentSerializer(instance)
        expected = {
            'embedded_list': [{'name': 'Joe'}],
            'embedded_map': {'Joe': {'age': 9}},
            'list_of_embedded_documents': [{'name': 'Joe'}]
        }
        assert serializer.data == expected

    def test_create(self):
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

        data = {
            'embedded_list': [{'name': 'Joe'}],
            'embedded_map': {'Joe': {'age': 9}},
            'list_of_embedded_documents': [{'name': 'Joe'}]
        }

        serializer = CompoundParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'embedded_list': [{'name': 'Joe'}],
            'embedded_map': {'Joe': {'age': 9}},
            'list_of_embedded_documents': [{'name': 'Joe'}]
        }
        assert serializer.data == expected

    def test_update(self):
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

        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )

        data = {
            'embedded_list': [{'name': 'Jack'}],
            'embedded_map': {'Joe': {'age': 10}},
            'list_of_embedded_documents': [{'name': 'Jack'}]
        }

        serializer = CompoundParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'embedded_list': [{'name': 'Jack'}],
            'embedded_map': {'Joe': {'age': 10}},
            'list_of_embedded_documents': [{'name': 'Jack'}]
        }
        assert serializer.data == expected


class TestNestedCompoundCustomizationReadOnlyIntegration(TestCase):
    def doCleanups(self):
        CompoundParentDocument.drop_collection()

    def test_parsing(self):
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

        input_data = {
            "foo": "x",
            "embedded_list": [{'name': 'Joe', 'age': 9}],
            "embedded_map": {'0': {'name': 'Joe', 'age': 9}},
            "list_of_embedded_documents": [{'name': 'Joe', 'age': 9}]
        }

        serializer = CompoundParentSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            "embedded_list": [{'age': 9}],
            "embedded_map": {'0': {'age': 9}},
            "list_of_embedded_documents": [{'age': 9}]
        }

        assert serializer.validated_data == expected

    def test_retrieval(self):
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

        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )
        serializer = CompoundParentSerializer(instance)
        expected = {
            'id': str(instance.id),
            'foo': 'x',
            'embedded_list': [{'name': 'Joe', 'age': 9}],
            'embedded_map': {'Joe': {'name': 'Joe', 'age': 9}},
            'list_of_embedded_documents': [{'name': 'Joe', 'age': 9}]
        }
        assert serializer.data == expected

    def test_create(self):
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

        data = {
            "foo": "bar",
            "embedded_list": [{'name': 'Joe', 'age': 9}],
            "embedded_map": {'0': {'name': 'Joe', 'age': 9}},
            "list_of_embedded_documents": [{'name': 'Joe', 'age': 9}]
        }

        serializer = CompoundParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'foo': None,
            'embedded_list': [{'name': None, 'age': 9}],
            'embedded_map': {'0': {'name': None, 'age': 9}},
            'list_of_embedded_documents': [{'name': None, 'age': 9}]
        }
        assert serializer.data == expected

    def test_update(self):
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

        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )

        data = {
            "foo": "y",
            "embedded_list": [{'name': 'Jack', 'age': 10}],
            "embedded_map": {'0': {'name': 'Jack', 'age': 10}},
            "list_of_embedded_documents": [{'name': 'Jack', 'age': 10}]
        }

        serializer = CompoundParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'foo': 'x',
            'id': str(instance.id),
            'embedded_list': [{'name': None, 'age': 10}],
            'embedded_map': {'0': {'name': None, 'age': 10}},
            'list_of_embedded_documents': [{'name': None, 'age': 10}]
        }
        assert serializer.data == expected


class TestNestedCompoundCustomizationExtraFieldKwargsIntegration(TestCase):
    def doCleanups(self):
        CompoundParentDocument.drop_collection()

    def test_parsing(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = ('__all__')
                depth = 1
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded_list.child.name': {'default': 'Johnny'},
                    'embedded_map.child.name': {'default': 'B'},
                    'list_of_embedded_documents.child.name': {'default': 'Good'},
                }

        input_data = {
            "embedded_list": [{'age': 9}],
            "embedded_map": {'0': {'age': 9}},
            "list_of_embedded_documents": [{'age': 9}]
        }

        serializer = CompoundParentSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            "foo": 'bar',
            "embedded_list": [{'name': 'Johnny', 'age': 9}],
            "embedded_map": {'0': {'name': 'B', 'age': 9}},
            "list_of_embedded_documents": [{'name': 'Good', 'age': 9}]
        }

        assert serializer.validated_data == expected

    def test_retrieval(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = ('__all__')
                depth = 1
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded_list.child.name': {'default': 'Johnny'},
                    'embedded_map.child.name': {'default': 'B'},
                    'list_of_embedded_documents.child.name': {'default': 'Good'}
                }

        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )
        serializer = CompoundParentSerializer(instance)
        expected = {
            'id': str(instance.id),
            'foo': 'x',
            'embedded_list': [{'name': 'Joe', 'age': 9}],
            'embedded_map': {'Joe': {'name': 'Joe', 'age': 9}},
            'list_of_embedded_documents': [{'name': 'Joe', 'age': 9}]
        }
        assert serializer.data == expected

    def test_create(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = ('__all__')
                depth = 1
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded_list.child.name': {'default': 'Johnny'},
                    'embedded_map.child.name': {'default': 'B'},
                    'list_of_embedded_documents.child.name': {'default': 'Good'}
                }

        data = {
            "foo": "bar",
            "embedded_list": [{'age': 9}],
            "embedded_map": {'0': {'age': 9}},
            "list_of_embedded_documents": [{'age': 9}]
        }

        serializer = CompoundParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'id': str(serializer.instance.id),
            'foo': 'bar',
            'embedded_list': [{'name': 'Johnny', 'age': 9}],
            'embedded_map': {'0': {'name': 'B', 'age': 9}},
            'list_of_embedded_documents': [{'name': 'Good', 'age': 9}]
        }
        assert serializer.data == expected

    def test_update(self):
        class CompoundParentSerializer(DocumentSerializer):
            class Meta:
                model = CompoundParentDocument
                fields = ('__all__')
                depth = 1
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded_list.child.name': {'default': 'Johnny'},
                    'embedded_map.child.name': {'default': 'B'},
                    'list_of_embedded_documents.child.name': {'default': 'Good'}
                }

        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )

        data = {
            "foo": "y",
            "embedded_list": [{'age': 10}],
            "embedded_map": {'0': {'age': 10}},
            "list_of_embedded_documents": [{'age': 10}]
        }

        serializer = CompoundParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'foo': 'y',
            'id': str(instance.id),
            'embedded_list': [{'name': 'Johnny', 'age': 10}],
            'embedded_map': {'0': {'name': 'B', 'age': 10}},
            'list_of_embedded_documents': [{'name': 'Good', 'age': 10}]
        }
        assert serializer.data == expected


class TestNestedCompoundCustomizationValidateMethodIntegration(TestCase):
    class CompoundParentSerializer(DocumentSerializer):
        class Meta:
            model = CompoundParentDocument
            fields = ('__all__')

        def validate_embedded_list__child__name(self, value):
            if len(value) < 4:
                raise ValidationError('Minimum 4 characters.')
            return value.title()

        def validated_embedded_map__child__name(self, value):
            if len(value) < 4:
                raise ValidationError('Minimum 4 characters.')
            return value.title()

        def validated_list_of_embedded_documents__child__name(self, value):
            if len(value) < 4:
                raise ValidationError('Minimum 4 characters.')
            return value.title()

    def doCleanups(self):
        CompoundParentDocument.drop_collection()

    def test_create_success(self):
        data = {
            "foo": 'x',
            "embedded_list": [{'name': 'Jack', 'age': 9}],
            "embedded_map": {'0': {'name': 'Jack', 'age': 9}},
            "list_of_embedded_documents": [{'name': 'Jack', 'age': 9}]
        }

        serializer = self.CompoundParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        expected = {
            'embedded_list': [{'name': u'Jack', 'age': 9}],
            'list_of_embedded_documents': [{'name': 'Jack', 'age': 9}],
            'foo': 'x',
            'id': str(serializer.instance.id),
            'embedded_map': {'0': {'name': 'Jack', 'age': 9}}
        }

        assert serializer.data == expected

    def test_create_fail(self):
        data = {
            "foo": "bar",
            "embedded_list": [{'name': 'Joe', 'age': 9}],
            "embedded_map": {'0': {'name': 'Joe', 'age': 9}},
            "list_of_embedded_documents": [{'name': 'Joe', 'age': 9}]
        }

        serializer = self.CompoundParentSerializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'embedded_list': {'name': [u'Minimum 4 characters.']}}

    def test_update_success(self):
        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )

        data = {
            "foo": "y",
            "embedded_list": [{'name': 'Jack', 'age': 10}],
            "embedded_map": {'0': {'name': 'Jack', 'age': 10}},
            "list_of_embedded_documents": [{'name': 'Jack', 'age': 10}]
        }

        serializer = self.CompoundParentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        expected = {
            'id': str(serializer.instance.id),
            'foo': 'y',
            "embedded_list": [{'name': 'Jack', 'age': 10}],
            "embedded_map": {'0': {'name': 'Jack', 'age': 10}},
            "list_of_embedded_documents": [{'name': 'Jack', 'age': 10}]
        }
        assert serializer.data == expected

    def test_update_fail(self):
        instance = CompoundParentDocument.objects.create(
            foo='x',
            embedded_list=[ChildDocument(name='Joe', age=9)],
            embedded_map={'Joe': ChildDocument(name='Joe', age=9)},
            list_of_embedded_documents=[ChildDocument(name='Joe', age=9)]
        )

        data = {
            "foo": "y",
            "embedded_list": [{'name': 'Jim', 'age': 10}],
            "embedded_map": {'0': {'name': 'Jim', 'age': 10}},
            "list_of_embedded_documents": [{'name': 'Jim', 'age': 10}]
        }

        serializer = self.CompoundParentSerializer(instance, data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'embedded_list': {'name': [u'Minimum 4 characters.']}}
