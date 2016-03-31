from django.test import TestCase

from mongoengine import Document, EmbeddedDocument, fields
from rest_framework.test import APITestCase, APIRequestFactory

from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine.viewsets import GenericViewSet
from rest_framework_mongoengine.contrib.patching import Patch, PatchModelMixin


class DumbEmbedded(EmbeddedDocument):
    name = fields.StringField()
    numb = fields.IntField()
    items = fields.ListField(fields.IntField())
    emb = fields.EmbeddedDocumentField('self')


class DumbDocument(Document):
    name = fields.StringField()
    int_fld = fields.IntField()
    lst_fld = fields.ListField()
    dct_fld = fields.DictField()
    intlst_fld = fields.ListField(fields.IntField())
    intdct_fld = fields.MapField(fields.IntField())
    emb = fields.EmbeddedDocumentField(DumbEmbedded)


class DumbSerializer(DocumentSerializer):
    class Meta:
        model = DumbDocument


class TestPatchParsing(TestCase):
    def test_nonlist(self):
        patch = Patch(data={'path': "/name", 'op': "set", 'value': "Foo"})
        assert not patch.is_valid()

    def test_nondict(self):
        patch = Patch(data=["xxx"])
        assert not patch.is_valid()

    def test_incomplete(self):
        patch = Patch(data=[{'path': "/name", 'value': "Foo"}])
        assert not patch.is_valid()

    def test_nonpath(self):
        patch = Patch(data=[{'path': "name", 'value': "Foo"}])
        assert not patch.is_valid()

    def test_parsing_path(self):
        patch = Patch(data=[
            {'path': "/name", 'op': "set", 'value': None},
            {'path': "/emb_fld/name", 'op': "set", 'value': None},
            {'path': "/lst_fld/0", 'op': "set", 'value': None},
            {'path': "/lst_fld/$", 'op': "set", 'value': None},
            {'path': "/emb_fld/emb/emb/name", 'op': "set", 'value': None}
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("name", ), 'op': "set", 'value': None},
            {'path': ("emb_fld", "name"), 'op': "set", 'value': None},
            {'path': ("lst_fld", "0"), 'op': "set", 'value': None},
            {'path': ("lst_fld", "$"), 'op': "set", 'value': None},
            {'path': ("emb_fld", "emb", "emb", "name"), 'op': "set", 'value': None},
        ]
        assert patch.validated_data == expected

    def test_parsing_path_fail(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/name", 'op': "set", 'value': None},
            {'path': "/bla", 'op': "set", 'value': None},
            {'path': "/name/bla", 'op': "set", 'value': None},
            {'path': "/emb/name/bla", 'op': "set", 'value': None},
        ])
        assert not patch.is_valid()
        assert patch.errors == [{}, {'path': "Missing elem: 'bla'"}, {'path': "Missing elem: 'bla'"}, {'path': "Missing elem: 'bla'"}]

    def test_parsing_values(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/name", 'op': "set", 'value': "123"},
            {'path': "/int_fld", 'op': "set", 'value': "123"},
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("name",), 'op': "set", 'value': "123"},
            {'path': ("int_fld",), 'op': "set", 'value': 123},
        ]
        assert patch.validated_data == expected

    def test_parsing_values_fail(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/name", 'op': "set", 'value': "xxx"},
            {'path': "/int_fld", 'op': "set", 'value': "xxx"},
        ])
        assert not patch.is_valid()
        assert patch.errors == [{}, ['A valid integer is required.']]

    def test_parsing_nested_values(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/emb/name", 'op': "set", 'value': "123"},
            {'path': "/emb/numb", 'op': "set", 'value': "123"},
            {'path': "/emb/emb/emb/name", 'op': "set", 'value': "123"},
            {'path': "/emb/emb/emb/numb", 'op': "set", 'value': "123"},
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("emb", "name"), 'op': "set", 'value': "123"},
            {'path': ("emb", "numb"), 'op': "set", 'value': 123},
            {'path': ("emb", "emb", "emb", "name"), 'op': "set", 'value': "123"},
            {'path': ("emb", "emb", "emb", "numb"), 'op': "set", 'value': 123},
        ]
        assert patch.validated_data == expected

    def test_parsing_item_values(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/lst_fld/1", 'op': "set", 'value': "123"},
            {'path': "/intlst_fld/1", 'op': "set", 'value': "123"},
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("lst_fld", "1"), 'op': "set", 'value': "123"},
            {'path': ("intlst_fld", "1"), 'op': "set", 'value': 123},
        ]
        assert patch.validated_data == expected

    def test_parsing_elem_values(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/dct_fld/item", 'op': "set", 'value': "123"},
            {'path': "/intdct_fld/item", 'op': "set", 'value': "123"}
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("dct_fld", "item"), 'op': "set", 'value': "123"},
            {'path': ("intdct_fld", "item"), 'op': "set", 'value': 123}
        ]
        assert patch.validated_data == expected

    def test_parsing_embedded(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/emb", 'op': "set", 'value': { 'name': "Foo", 'numb': "123"}}
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("emb",), 'op': "set", 'value': DumbEmbedded(name="Foo", numb=123)}
        ]
        assert patch.validated_data == expected


class TestPatchSerializedParsing(TestCase):
    def test_field(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/int_fld", 'op': "set", 'value': "123"},
        ])
        assert patch.is_valid()
        expected = [
            {'path': ("int_fld", ), 'op': "set", 'value': 123},
        ]
        assert patch.validated_data == expected

    def test_typed_nested(self):
        patch = Patch(DumbSerializer, data=[
            {'path': "/int_fld", 'op': "set", 'value': "123"},
        ])
        assert patch.is_valid()
        expected = [
            {'path': ("int_fld", ), 'op': "set", 'value': 123},
        ]
        assert patch.validated_data == expected


class TestView(PatchModelMixin, GenericViewSet):
    queryset = DumbDocument.objects


class TestPatchingView(APITestCase):
    client_class = APIRequestFactory

    def setUp(self):
        self.objects = [
            DumbDocument.objects.create(name="dumb1", int_fld=1, emb_fld=DumbEmbedded(items=['a', 'b', 'c'])),
            DumbDocument.objects.create(name="dumb2", int_fld=2, emb_fld=DumbEmbedded(items=['b', 'c', 'd'])),
            DumbDocument.objects.create(name="dumb3", int_fld=3, emb_fld=DumbEmbedded(items=['d', 'e', 'f']))
        ]

    def tearDown(self):
        DumbDocument.drop_collection()

    def test_obj_patch_plain(self):
        patch = [{'path': '/foo', 'op': 'set', 'value': 200}]

        view = TestView.as_view({'patch': 'modify_obj'})
        req = self.client.patch("", patch, format='json')
        res = view(req, id=self.objects[1].id)
        assert res.status_code == 204

        for o in self.objects:
            o.reload()
        assert [o.int_fld for o in self.objects] == [1, 200, 3]

    def test_obj_patch_compl(self):
        patch = [{'path': '/emb_fld/items', 'op': 'push', 'value': 'z'},
                 {'path': '/int_fld', 'op': 'inc', 'value': 10}]

        view = TestView.as_view({'patch': 'modify_obj'})
        req = self.client.patch("", patch, format='json')
        res = view(req, id=self.objects[1].id)
        assert res.status_code == 204

        for o in self.objects:
            o.reload()
        assert [o.int_fld for o in self.objects] == [1, 12, 3]
        assert [o.emb_fld.items for o in self.objects] == [['a', 'b', 'c'], ['b', 'c', 'd', 'z'], ['d', 'e', 'f']]

    def test_obj_patch_same(self):
        patch = [{'path': '/emb_fld/items', 'op': 'pull', 'value': 'a'},
                 {'path': '/emb_fld/items', 'op': 'push', 'value': 'x'},
                 {'path': '/emb_fld/items', 'op': 'push', 'value': 'y'}]

        view = TestView.as_view({'patch': 'modify_obj'})
        req = self.client.patch("", patch, format='json')
        res = view(req, id=self.objects[0].id)
        assert res.status_code == 204

        for o in self.objects:
            o.reload()
        assert [o.emb_fld.items for o in self.objects] == [['b', 'c', 'x', 'y'], ['b', 'c', 'd'], ['d', 'e', 'f']]
