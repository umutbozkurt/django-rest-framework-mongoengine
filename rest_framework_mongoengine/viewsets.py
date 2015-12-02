"""
The module description
"""

from rest_framework import mixins
from rest_framework.viewsets import ViewSetMixin
from rest_framework_mongoengine.generics import GenericAPIView


class GenericViewSet(ViewSetMixin, GenericAPIView):
    """ Replication of DRF GenericViewSet """

class ModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    """ Replication of DRF ModelViewSet """
    pass


class ReadOnlyModelViewSet(mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    """ Replication of DRF ReadOnlyModelViewSet """
    pass
