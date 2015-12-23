from __future__ import unicode_literals

from django.test import TestCase
from mongoengine import Document, fields
from rest_framework_mongoengine.routers import DefaultRouter, SimpleRouter
from rest_framework_mongoengine.viewsets import GenericViewSet


class DumbModel(Document):
    foo = fields.StringField()


class DumbViewSet(GenericViewSet):
    queryset = DumbModel.objects

    def list(self, request):
        pass

    def retrieve(self, request, id):
        pass


class TestRouters(TestCase):
    def test_simple(self):
        router = SimpleRouter()
        router.register('dumb', DumbViewSet)
        urlnames = set(map(lambda r: r.name, router.urls))
        assert urlnames == set(('dumbmodel-list', 'dumbmodel-detail'))

    def test_default(self):
        router = DefaultRouter()
        router.register('dumb', DumbViewSet)
        urlnames = set(map(lambda r: r.name, router.urls))
        assert urlnames == set(('api-root', 'dumbmodel-list', 'dumbmodel-detail'))
