from django.test import TestCase
from mongoengine import Document, EmbeddedDocument, fields
from rest_framework.test import APIRequestFactory, APITestCase

from rest_framework_mongoengine.contrib.patching import Patch, PatchModelMixin
from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine.viewsets import GenericViewSet

from .models import DumbEmbedded


class PatchingDumbDocument(Document):
    name = fields.StringField()
    int_fld = fields.IntField()
    lst_fld = fields.ListField()
    dct_fld = fields.DictField()
    intlst_fld = fields.ListField(fields.IntField())
    intdct_fld = fields.MapField(fields.IntField())
    emb = fields.EmbeddedDocumentField(DumbEmbedded)
    emb_lst = fields.EmbeddedDocumentListField(DumbEmbedded)


class DumbSerializer(DocumentSerializer):
    class Meta:
        model = PatchingDumbDocument


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
            {'path': "/emb_fld/emb/emb/name", 'op': "set", 'value': None}
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("name", ), 'op': "set", 'value': None},
            {'path': ("emb_fld", "name"), 'op': "set", 'value': None},
            {'path': ("lst_fld", "0"), 'op': "set", 'value': None},
            {'path': ("emb_fld", "emb", "emb", "name"), 'op': "set", 'value': None},
        ]
        assert patch.validated_data == expected

    def test_parsing_path_fail(self):
        patch = Patch(DumbSerializer(), data=[
            {'path': "/name", 'op': "set", 'value': None},
            {'path': "/bla", 'op': "set", 'value': None},
            {'path': "/name/bla", 'op': "set", 'value': None},
            {'path': "/emb/name/bla", 'op': "set", 'value': None},
        ])
        assert not patch.is_valid()
        assert patch.errors == [{}, {'path': "Missing elem: 'bla'"}, {'path': "Missing elem: 'bla'"}, {'path': "Missing elem: 'bla'"}]

    def test_parsing_values(self):
        patch = Patch(DumbSerializer(), data=[
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
        patch = Patch(DumbSerializer(), data=[
            {'path': "/name", 'op': "set", 'value': "xxx"},
            {'path': "/int_fld", 'op': "set", 'value': "xxx"},
        ])
        assert not patch.is_valid()
        assert patch.errors == [{}, ['A valid integer is required.']]

    def test_parsing_nested_values(self):
        patch = Patch(DumbSerializer(), data=[
            {'path': "/emb/name", 'op': "set", 'value': "123"},
            {'path': "/emb/foo", 'op': "set", 'value': "123"},
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("emb", "name"), 'op': "set", 'value': "123"},
            {'path': ("emb", "foo"), 'op': "set", 'value': 123},
        ]
        assert patch.validated_data == expected

    def test_parsing_item_values(self):
        patch = Patch(DumbSerializer(), data=[
            {'path': "/lst_fld/1", 'op': "set", 'value': "123"},
            {'path': "/intlst_fld/1", 'op': "set", 'value': "123"},
            {'path': "/intlst_fld", 'op': "push", 'value': "123"},
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("lst_fld", "1"), 'op': "set", 'value': "123"},
            {'path': ("intlst_fld", "1"), 'op': "set", 'value': 123},
            {'path': ("intlst_fld",), 'op': "push", 'value': 123},
        ]
        assert patch.validated_data == expected

    def test_parsing_elem_values(self):
        patch = Patch(DumbSerializer(), data=[
            {'path': "/dct_fld/item", 'op': "set", 'value': "123"},
            {'path': "/intdct_fld/item", 'op': "set", 'value': "123"}
        ])
        assert patch.is_valid(), patch.errors
        expected = [
            {'path': ("dct_fld", "item"), 'op': "set", 'value': "123"},
            {'path': ("intdct_fld", "item"), 'op': "set", 'value': 123}
        ]
        assert patch.validated_data == expected


class TestPatchApplying(TestCase):
    def tearDown(self):
        PatchingDumbDocument.drop_collection()

    def test_patch_obj(self):
        objects = [
            PatchingDumbDocument.objects.create(name="dumb1", int_fld=1, lst_fld=['a', 'b', 'c'], emb=DumbEmbedded(name="emb1")),
            PatchingDumbDocument.objects.create(name="dumb2", int_fld=2, lst_fld=['b', 'c', 'd'], emb=DumbEmbedded(name="emb2")),
            PatchingDumbDocument.objects.create(name="dumb3", int_fld=3, lst_fld=['d', 'e', 'f'], emb=DumbEmbedded(name="emb3"))
        ]

        patch = Patch(data=[{'path': '/int_fld', 'op': 'inc', 'value': 100},
                            {'path': '/lst_fld', 'op': 'push', 'value': 'z'},
                            {'path': '/dct_fld/foo', 'op': 'set', 'value': "f"},
                            {'path': '/dct_fld/bar', 'op': 'set', 'value': "b"},
                            {'path': '/emb/name', 'op': 'set', 'value': "Foo"}])

        assert patch.is_valid(), patch.errors

        obj = PatchingDumbDocument.objects.get(name="dumb2")
        patch.update_queryset(obj)

        for o in objects:
            o.reload()
        assert [o.int_fld for o in objects] == [1, 102, 3]
        assert [o.lst_fld for o in objects] == [['a', 'b', 'c'], ['b', 'c', 'd', 'z'], ['d', 'e', 'f']]
        assert [o.dct_fld for o in objects] == [{}, {'foo': 'f', 'bar': 'b'}, {}]
        assert [o.emb.name for o in objects] == ["emb1", "Foo", "emb3"]

    def test_patch_set(self):
        objects = [
            PatchingDumbDocument.objects.create(name="dumb1", int_fld=1, lst_fld=['a', 'b', 'c'], emb=DumbEmbedded(name="emb1")),
            PatchingDumbDocument.objects.create(name="dumb2", int_fld=2, lst_fld=['b', 'c', 'd'], emb=DumbEmbedded(name="emb2")),
            PatchingDumbDocument.objects.create(name="dumb3", int_fld=3, lst_fld=['d', 'e', 'f'], emb=DumbEmbedded(name="emb3"))
        ]

        patch = Patch(data=[{'path': '/int_fld', 'op': 'inc', 'value': 100},
                            {'path': '/lst_fld', 'op': 'push', 'value': 'z'},
                            {'path': '/emb/name', 'op': 'set', 'value': "Foo"}])

        assert patch.is_valid(), patch.errors

        queryset = PatchingDumbDocument.objects.all()
        patch.update_queryset(queryset)

        for o in objects:
            o.reload()
        assert [o.int_fld for o in objects] == [101, 102, 103]
        assert [o.lst_fld for o in objects] == [['a', 'b', 'c', 'z'], ['b', 'c', 'd', 'z'], ['d', 'e', 'f', 'z']]
        assert [o.emb.name for o in objects] == ["Foo", "Foo", "Foo"]

    def test_patch_matched(self):
        objects = [
            PatchingDumbDocument.objects.create(
                name="dumb1",
                emb_lst=[
                    DumbEmbedded(name="dumb1emb1", foo=11),
                    DumbEmbedded(name="dumb1emb2", foo=12),
                    DumbEmbedded(name="dumb1emb3", foo=13)
                ]
            ),
            PatchingDumbDocument.objects.create(
                name="dumb2",
                emb_lst=[
                    DumbEmbedded(name="dumb2emb1", foo=21),
                    DumbEmbedded(name="dumb2emb2", foo=22),
                    DumbEmbedded(name="dumb2emb3", foo=23)
                ]
            ),
            PatchingDumbDocument.objects.create(
                name="dumb3",
                emb_lst=[
                    DumbEmbedded(name="dumb3emb1", foo=31),
                    DumbEmbedded(name="dumb3emb2", foo=32),
                    DumbEmbedded(name="dumb3emb3", foo=33)
                ]
            ),
        ]

        patch = Patch(data=[{'path': "/emb_lst/S/name", 'op': 'set', 'value': "winner"}])
        assert patch.is_valid(), patch.errors

        queryset = PatchingDumbDocument.objects.filter(emb_lst__foo=22)
        patch.update_queryset(queryset)
        for o in objects:
            o.reload()

        for o in objects:
            for e in o.emb_lst:
                assert e.foo != 22 or e.name == "winner"


class TestView(PatchModelMixin, GenericViewSet):
    serializer_class = DumbSerializer
    queryset = PatchingDumbDocument.objects


class TestPatchingView(APITestCase):
    client_class = APIRequestFactory

    def tearDown(self):
        PatchingDumbDocument.drop_collection()

    def test_patch_obj(self):
        objects = [
            PatchingDumbDocument.objects.create(name="dumb1", lst_fld=['a', 'b', 'c']),
            PatchingDumbDocument.objects.create(name="dumb2", lst_fld=['b', 'c', 'd']),
            PatchingDumbDocument.objects.create(name="dumb3", lst_fld=['d', 'e', 'f'])
        ]

        patch = [{'path': '/lst_fld', 'op': 'push', 'value': 'z'}]

        view = TestView.as_view({'patch': 'modify_obj'})
        req = self.client.patch("", patch, format='json')
        res = view(req, id=objects[1].id)
        assert res.status_code == 204

        for o in objects:
            o.reload()
        assert [o.lst_fld for o in objects] == [['a', 'b', 'c'], ['b', 'c', 'd', 'z'], ['d', 'e', 'f']]

    def test_patch_set(self):
        objects = [
            PatchingDumbDocument.objects.create(name="dumb1", lst_fld=['a', 'b', 'c']),
            PatchingDumbDocument.objects.create(name="dumb2", lst_fld=['b', 'c', 'd']),
            PatchingDumbDocument.objects.create(name="dumb3", lst_fld=['d', 'e', 'f'])
        ]
        patch = [{'path': '/lst_fld', 'op': 'push', 'value': 'z'}]

        view = TestView.as_view({'patch': 'modify_set'})
        req = self.client.patch("", patch, format='json')
        res = view(req)
        assert res.status_code == 204

        for o in objects:
            o.reload()
        assert [o.lst_fld for o in objects] == [['a', 'b', 'c', 'z'], ['b', 'c', 'd', 'z'], ['d', 'e', 'f', 'z']]
