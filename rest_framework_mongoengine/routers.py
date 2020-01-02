from rest_framework import routers as drf_routers


class MongoRouterMixin(object):
    """ Mixin for mongo-routers.

    Determines base_name from mongo queryset
    """

    def get_default_basename(self, viewset):
        queryset = getattr(viewset, 'queryset', None)
        assert queryset is not None, ('`base_name` argument not specified, and could '
                                      'not automatically determine the name from the viewset, as '
                                      'it does not have a `.queryset` attribute.')
        return queryset._document.__name__.lower()


class SimpleRouter(MongoRouterMixin, drf_routers.SimpleRouter):
    """ Adaptation of DRF SimpleRouter """
    pass


class DefaultRouter(MongoRouterMixin, drf_routers.DefaultRouter):
    """ Adaptation of DRF DefaultRouter """
    pass
