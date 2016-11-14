from __future__ import unicode_literals

from django.test import TestCase
from rest_framework import permissions, status
from rest_framework.test import APIRequestFactory

from rest_framework_mongoengine import generics
from rest_framework_mongoengine.serializers import DocumentSerializer

from .models import DumbDocument


class DumbSerializer(DocumentSerializer):
    class Meta:
        model = DumbDocument
        fields = '__all__'


class ListView(generics.ListAPIView):
    queryset = DumbDocument.objects
    serializer_class = DumbSerializer


class BasicPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.name != 'baz'


class RetrView(generics.RetrieveAPIView):
    queryset = DumbDocument.objects
    serializer_class = DumbSerializer
    permission_classes = [BasicPermission]


class TestBasicViews(TestCase):
    client_class = APIRequestFactory

    def setUp(self):
        """
        Create 3 DumbDocument instances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            DumbDocument(name=item).save()
        self.objects = DumbDocument.objects
        self.data = [
            {'id': str(obj.id), 'name': obj.name, 'foo': None}
            for obj in self.objects.all()
        ]

    def doCleaups(self):
        DumbDocument.drop_collection()

    def test_list(self):
        view = ListView.as_view()
        request = self.client.get('/')
        response = view(request).render()
        assert response.status_code == status.HTTP_200_OK
        assert response.data == self.data

    def test_retr(self):
        view = RetrView.as_view()
        oid = self.objects[1].id
        request = self.client.get('/' + str(oid))
        response = view(request, id=oid).render()
        assert response.status_code == status.HTTP_200_OK
        assert response.data == self.data[1]

    def test_retr_denied(self):
        view = RetrView.as_view()
        oid = self.objects[2].id
        request = self.client.get('/' + str(oid))
        response = view(request, id=oid).render()
        assert response.status_code == status.HTTP_403_FORBIDDEN
