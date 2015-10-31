import pytest

from django.test import TestCase

from mongoengine import Document, fields

class GeoModel(Document):
    geo_point_field = fields.PointField()
    geo_line_field = fields.LineStringField()
    geo_polygon_field = fields.PolygonField()
    geo_multi_point_field = fields.MultiPointField()
    geo_multi_line_field = fields.MultiLineStringField()
    geo_multi_poly_field = fields.MultiPolygonField()


class TestGeoMapping(TestCase):
    def test_mapping(self):
        pytest.skip("TODO")
