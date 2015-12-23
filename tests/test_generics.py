from __future__ import unicode_literals

from django.test import TestCase
from mongoengine import Document, fields
from rest_framework import permissions, status
from rest_framework.test import APIRequestFactory
from rest_framework_mongoengine import generics
from rest_framework_mongoengine.serializers import DocumentSerializer


class BasicModel(Document):
    text = fields.StringField()


class BasicSerializer(DocumentSerializer):
    class Meta:
        model = BasicModel


class ListView(generics.ListAPIView):
    queryset = BasicModel.objects
    serializer_class = BasicSerializer


class BasicPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.text != 'baz'


class RetrView(generics.RetrieveAPIView):
    queryset = BasicModel.objects
    serializer_class = BasicSerializer
    permission_classes = [BasicPermission]


class TestBasicViews(TestCase):
    client_class = APIRequestFactory

    def setUp(self):
        """
        Create 3 BasicModel instances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': str(obj.id), 'text': obj.text}
            for obj in self.objects.all()
        ]

    def tearDown(self):
        BasicModel.drop_collection()

    def test_list(self):
        view = ListView.as_view()
        request = self.client.get('/')
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

    def test_retr(self):
        view = RetrView.as_view()
        oid = self.objects[1].id
        request = self.client.get('/' + str(oid))
        response = view(request, id=oid).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data[1])

    def test_retr_denied(self):
        view = RetrView.as_view()
        oid = self.objects[2].id
        request = self.client.get('/' + str(oid))
        response = view(request, id=oid).render()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
