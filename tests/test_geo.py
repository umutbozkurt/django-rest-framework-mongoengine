from django.test import TestCase
from mongoengine import Document, fields

from rest_framework_mongoengine.fields import GeoJSONField, GeoPointField
from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import FieldTest, dedent


class TestGeoPointField(FieldTest, TestCase):
    field = GeoPointField()
    valid_inputs = [
        ([0.1, 0.2], [0.1, 0.2]),
        ([1, 2], [1.0, 2.0]),
        (["0.1", "0.2"], [0.1, 0.2])
    ]
    invalid_inputs = [
        (0.1, "must be a list"),
        ([0.1, 0.2, 0.3], "must be a two-dimensional"),
        (["xxx", "xxx"], "must be float or int")
    ]
    outputs = [
        ([0.1, 0.2], [0.1, 0.2])
    ]


class TestPointField(FieldTest, TestCase):
    field = GeoJSONField('Point')
    valid_inputs = [
        ([0.1, 0.2], [0.1, 0.2]),
        ({'type': "Point", 'coordinates': [0.1, 0.2]}, [0.1, 0.2])
    ]
    invalid_inputs = [
        (0.1, "must be a geojson geometry or a geojson coordinates"),
        ({'type': "Polygon", 'coordinates': [[[0.1, 0.2], [0.1, 0.2]]]}, "expected to be 'Point'"),
        ({'type': "Point", 'coordinates': 0.1}, "can only accept lists"),  # from mongoengine
        ([0.1, 0.2, 0.3], "must be a two-dimensional"),  # from mongoengine
        (["xxx", "xxx"], "must be float or int")  # from mongoengine
    ]
    outputs = [
        ([0.1, 0.2], {'type': "Point", 'coordinates': [0.1, 0.2]})
    ]


class TestMultiPointField(FieldTest, TestCase):
    field = GeoJSONField('MultiPoint')
    valid_inputs = [
        ([[0.1, 0.2], [0.3, 0.4]], [[0.1, 0.2], [0.3, 0.4]]),
        ({'type': "MultiPoint", 'coordinates': [[0.1, 0.2], [0.3, 0.4]]}, [[0.1, 0.2], [0.3, 0.4]])
    ]
    invalid_inputs = [
        (0.1, "must be a geojson geometry or a geojson coordinates"),
        ({'type': "Point", 'coordinates': [0.1, 0.2]}, "expected to be 'MultiPoint'"),
        ({'type': "MultiPoint", 'coordinates': 0.1}, "can only accept lists"),  # from mongoengine
        ([0.1, 0.2, 0.3, 0.4], "must contain at least one"),  # from mongoengine
        ([[0.1, 0.2], [0.3, 0.4, 0.5]], "must be a two-dimensional"),  # from mongoengine
        ([[0.1, 0.2], ["xxx", "xxx"]], "must be float or int")  # from mongoengine
    ]
    outputs = [
        ([[0.1, 0.2], [0.3, 0.4]], {'type': "MultiPoint", 'coordinates': [[0.1, 0.2], [0.3, 0.4]]})
    ]


class TestLineField(FieldTest, TestCase):
    field = GeoJSONField('LineString')
    valid_inputs = [
        ([[0.1, 0.2], [0.3, 0.4]], [[0.1, 0.2], [0.3, 0.4]]),
        ({'type': "LineString", 'coordinates': [[0.1, 0.2], [0.3, 0.4]]}, [[0.1, 0.2], [0.3, 0.4]])
    ]
    invalid_inputs = [
        (0.1, "must be a geojson geometry or a geojson coordinates"),
        ({'type': "Point", 'coordinates': [0.1, 0.2]}, "expected to be 'LineString'"),
        ({'type': "LineString", 'coordinates': 0.1}, "can only accept lists"),  # from mongoengine
        ([0.1, 0.2, 0.3, 0.4], "must contain at least one"),  # from mongoengine
        ([[0.1, 0.2], [0.3, 0.4, 0.5]], "must be a two-dimensional"),  # from mongoengine
        ([[0.1, 0.2], ["xxx", "xxx"]], "must be float or int")  # from mongoengine
    ]
    outputs = [
        ([[0.1, 0.2], [0.3, 0.4]], {'type': "LineString", 'coordinates': [[0.1, 0.2], [0.3, 0.4]]})
    ]


class TestMultiLineField(FieldTest, TestCase):
    field = GeoJSONField('MultiLineString')
    valid_inputs = [
        ([[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]], [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]]),
        ({'type': 'MultiLineString', 'coordinates': [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]]}, [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]]),
    ]
    invalid_inputs = [
        (0.1, "must be a geojson geometry or a geojson coordinates"),
        ({'type': "Point", 'coordinates': [0.1, 0.2]}, "expected to be 'MultiLineString'"),
        ({'type': "MultiLineString", 'coordinates': 0.1}, "can only accept lists"),  # from mongoengine
        ([0.1, 0.2, 0.3, 0.4], "must contain at least one"),  # from mongoengine
        ([[[0.1, 0.2], [0.3, 0.4, 0.5]]], "must be a two-dimensional"),  # from mongoengine
        ([[[0.1, 0.2], ["xxx", "xxx"]]], "must be float or int"),  # from mongoengine
    ]
    outputs = [
        ([[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]], {'type': 'MultiLineString', 'coordinates': [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]]}),
    ]


class TestPolyField(FieldTest, TestCase):
    field = GeoJSONField('Polygon')
    valid_inputs = [
        ([[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]], [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]),
        ({'type': 'Polygon', 'coordinates': [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]}, [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]),
    ]
    invalid_inputs = [
        (0.1, "must be a geojson geometry or a geojson coordinates"),
        ({'type': "Point", 'coordinates': [0.1, 0.2]}, "expected to be 'Polygon'"),
        ({'type': "Polygon", 'coordinates': 0.1}, "can only accept lists"),  # from mongoengine
        ([0.1, 0.2, 0.3, 0.4], "must contain at least one"),  # from mongoengine
        ([[[0.1, 0.2], [0.3, 0.4, 0.5]]], "must be a two-dimensional"),  # from mongoengine
        ([[[0.1, 0.2], ["xxx", "xxx"]]], "must be float or int"),  # from mongoengine
        ([[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]], "must start and end"),  # from mongoengine
    ]
    outputs = [
        ([[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]], {'type': 'Polygon', 'coordinates': [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]}),
    ]


class TestMultiPolyField(FieldTest, TestCase):
    field = GeoJSONField('MultiPolygon')
    valid_inputs = [
        ([[[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]], [[[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]]),
        ({'type': 'MultiPolygon', 'coordinates': [[[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]]}, [[[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]]),
    ]
    invalid_inputs = [
        (0.1, "must be a geojson geometry or a geojson coordinates"),
        ({'type': "Point", 'coordinates': [0.1, 0.2]}, "expected to be 'MultiPolygon'"),
        ({'type': "MultiPolygon", 'coordinates': 0.1}, "can only accept lists"),  # from mongoengine
        ([0.1, 0.2, 0.3, 0.4], "must contain at least one"),  # from mongoengine
        ([[[[0.1, 0.2], [0.3, 0.4, 0.5]]]], "must be a two-dimensional"),  # from mongoengine
        ([[[[0.1, 0.2], ["xxx", "xxx"]]]], "must be float or int"),  # from mongoengine
        ([[[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]]], "must start and end"),  # from mongoengine
    ]
    outputs = [
        ([[[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]], {'type': 'MultiPolygon', 'coordinates': [[[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.1, 0.2]]]]}),
    ]


class GeoDoc(Document):
    geo_point_field = fields.GeoPointField()
    point_field = fields.PointField()
    line_field = fields.LineStringField()
    poly_field = fields.PolygonField()
    multi_point_field = fields.MultiPointField()
    multi_line_field = fields.MultiLineStringField()
    multi_poly_field = fields.MultiPolygonField()


class TestGeoMapping(TestCase):
    def test_mapping(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GeoDoc
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                geo_point_field = GeoPointField(required=False)
                point_field = GeoJSONField(geo_type='Point', required=False)
                line_field = GeoJSONField(geo_type='LineString', required=False)
                poly_field = GeoJSONField(geo_type='Polygon', required=False)
                multi_point_field = GeoJSONField(geo_type='MultiPoint', required=False)
                multi_line_field = GeoJSONField(geo_type='MultiLineString', required=False)
                multi_poly_field = GeoJSONField(geo_type='MultiPolygon', required=False)
        """)
        assert repr(TestSerializer()) == expected
