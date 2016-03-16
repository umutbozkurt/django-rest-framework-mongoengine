from __future__ import unicode_literals

from django.test import TestCase
from mongoengine import Document, fields

from rest_framework_mongoengine.routers import DefaultRouter, SimpleRouter
from rest_framework_mongoengine.viewsets import GenericViewSet

from .models import DumbDocument


class DumbViewSet(GenericViewSet):
    queryset = DumbDocument.objects

    def list(self, request):
        pass

    def retrieve(self, request, id):
        pass


class TestRouters(TestCase):
    def test_simple(self):
        router = SimpleRouter()
        router.register('dmb', DumbViewSet)
        urlnames = set(map(lambda r: r.name, router.urls))
        assert urlnames == set(('dumbdocument-list', 'dumbdocument-detail'))

    def test_default(self):
        router = DefaultRouter()
        router.register('dmb', DumbViewSet)
        urlnames = set(map(lambda r: r.name, router.urls))
        assert urlnames == set(('api-root', 'dumbdocument-list', 'dumbdocument-detail'))
