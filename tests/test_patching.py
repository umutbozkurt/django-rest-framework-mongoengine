from django.test import TestCase

from mongoengine import Document, EmbeddedDocument, fields
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework_mongoengine.viewsets import GenericViewSet

from rest_framework_mongoengine.patching import Patch, PatchModelMixin


class MockEmbedded(EmbeddedDocument):
    items = fields.ListField(fields.StringField())


class MockDocument(Document):
    name = fields.StringField()
    foo = fields.IntField()
    bar = fields.EmbeddedDocumentField(MockEmbedded)


class TestPatchParsing(TestCase):
    def test_nonlist(self):
        patch = Patch(data={'path': "/foo", 'op': "set", 'value': 123})
        assert not patch.is_valid()

    def test_nondict(self):
        patch = Patch(data=["xxx"])
        assert not patch.is_valid()

    def test_incomplete(self):
        patch = Patch(data=[{'path': "/foo", 'value': "Foo"}])
        assert not patch.is_valid()

    def test_nonpath(self):
        patch = Patch(data=[{'path': "foo", 'value': "Foo"}])
        assert not patch.is_valid()

    def test_parsing(self):
        patch = Patch(data=[
            {'path': "/foo", 'op': "set", 'value': 123},
            {'path': "/bar/items", 'op': "push", 'value': "Bar"}
        ])

        assert patch.is_valid()
        expected = [
            ('set__foo', 123),
            ('push__bar__items', "Bar")
        ]
        assert patch.validated_data == expected


class TestView(PatchModelMixin, GenericViewSet):
    queryset = MockDocument.objects


class TestPatchingView(APITestCase):
    client_class = APIRequestFactory

    def setUp(self):
        self.objects = [
            MockDocument.objects.create(name="dumb1", foo=1, bar=MockEmbedded(items=['a', 'b', 'c'])),
            MockDocument.objects.create(name="dumb2", foo=2, bar=MockEmbedded(items=['b', 'c', 'd'])),
            MockDocument.objects.create(name="dumb3", foo=3, bar=MockEmbedded(items=['d', 'e', 'f']))
        ]

    def tearDown(self):
        MockDocument.drop_collection()

    def test_obj_patch_plain(self):
        patch = [{'path': '/foo', 'op': 'set', 'value': 200}]

        view = TestView.as_view({'patch': 'modify_obj'})
        req = self.client.patch("", patch, format='json')
        res = view(req, id=self.objects[1].id)
        assert res.status_code == 204

        for o in self.objects:
            o.reload()
        assert [o.foo for o in self.objects] == [1, 200, 3]

    def test_obj_patch_compl(self):
        patch = [{'path': '/bar/items', 'op': 'push', 'value': 'z'},
                 {'path': '/foo', 'op': 'inc', 'value': 10}]

        view = TestView.as_view({'patch': 'modify_obj'})
        req = self.client.patch("", patch, format='json')
        res = view(req, id=self.objects[1].id)
        assert res.status_code == 204

        for o in self.objects:
            o.reload()
        assert [o.foo for o in self.objects] == [1, 12, 3]
        assert [o.bar.items for o in self.objects] == [['a', 'b', 'c'], ['b', 'c', 'd', 'z'], ['d', 'e', 'f']]

    def test_obj_patch_same(self):
        patch = [{'path': '/bar/items', 'op': 'pull', 'value': 'a'},
                 {'path': '/bar/items', 'op': 'push', 'value': 'x'},
                 {'path': '/bar/items', 'op': 'push', 'value': 'y'}]

        view = TestView.as_view({'patch': 'modify_obj'})
        req = self.client.patch("", patch, format='json')
        res = view(req, id=self.objects[0].id)
        assert res.status_code == 204

        for o in self.objects:
            o.reload()
        assert [o.bar.items for o in self.objects] == [['b', 'c', 'x', 'y'], ['b', 'c', 'd'], ['d', 'e', 'f']]
