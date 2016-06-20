from rest_framework import mixins
from rest_framework.viewsets import ViewSetMixin

from rest_framework_mongoengine.generics import GenericAPIView


class GenericViewSet(ViewSetMixin, GenericAPIView):
    """ Adaptation of DRF GenericViewSet """
    pass


class ModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    """ Adaptation of DRF ModelViewSet """
    pass


class ReadOnlyModelViewSet(mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    """ Adaptation of DRF ReadOnlyModelViewSet """
    pass
