"""
The `ModelSerializer` and `HyperlinkedModelSerializer` classes are essentially
shortcuts for automatically creating serializers based on a given model class.

These tests deal with ensuring that we correctly map the model fields onto
an appropriate set of serializer fields for each case.
"""
from __future__ import unicode_literals

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from bson import ObjectId
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from mongoengine import Document, fields
from rest_framework import serializers
from rest_framework.compat import unicode_repr
from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class CustomField(fields.BaseField):
    pass


class OneFieldModel(Document):
    str_field = fields.StringField()


class AutoFieldModel(Document):
    auto_field = fields.SequenceField(primary_key=True)


class RegularModel(Document):
    """
    A model class for testing regular flat fields.
    """
    str_field = fields.StringField()
    url_field = fields.URLField()
    email_field = fields.EmailField()
    int_field = fields.IntField()
    long_field = fields.LongField()
    float_field = fields.FloatField()
    boolean_field = fields.BooleanField()
    nullboolean_field = fields.BooleanField(null=True)
    date_field = fields.DateTimeField()
    complexdate_field = fields.ComplexDateTimeField()
    uuid_field = fields.UUIDField()
    id_field = fields.ObjectIdField()
    decimal_field = fields.DecimalField()

    custom_field = CustomField()

    # TODO
    # dynamic_field = fields.DynamicField()
    # bin_field = fields.BinaryField()
    # file_field = fields.FileField()
    # image_field = fields.ImageField()

    def method(self):
        return 'method'


COLOR_CHOICES = (('red', 'Red'), ('blue', 'Blue'), ('green', 'Green'))


class FieldOptionsModel(Document):
    required_field = fields.IntField(required=True)
    null_field = fields.IntField(null=True)
    choices_field = fields.StringField(choices=COLOR_CHOICES)
    length_limit_field = fields.StringField(min_length=3, max_length=12)
    value_limit_field = fields.IntField(min_value=3, max_value=12)
    decimal_field = fields.DecimalField(precision=4, max_value=9999)

DECIMAL_CHOICES = (('low', Decimal('0.1')), ('medium', Decimal('0.5')), ('high', Decimal('0.9')))


class ComplexChoicesModel(Document):
    choices_field_with_nonstandard_args = fields.DecimalField(precision=1, choices=DECIMAL_CHOICES, verbose_name='A label')


class TestRegularFieldMappings(TestCase):
    maxDiff = 10000

    def test_regular_fields(self):
        """
        Model fields should map to their equivelent serializer fields.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                str_field = CharField(required=False)
                url_field = URLField(required=False)
                email_field = EmailField(required=False)
                int_field = IntegerField(required=False)
                long_field = IntegerField(required=False)
                float_field = FloatField(required=False)
                boolean_field = BooleanField(required=False)
                nullboolean_field = NullBooleanField(required=False)
                date_field = DateTimeField(required=False)
                complexdate_field = DateTimeField(required=False)
                uuid_field = UUIDField(required=False)
                id_field = ObjectIdField(required=False)
                decimal_field = DecimalField(decimal_places=2, max_digits=65536, required=False)
                custom_field = DocumentField(model_field=<tests.test_1basic.CustomField: custom_field>, required=False)
        """)

        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_meta_fields(self):
        """
        Serializer should respect Meta.fields
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel
                fields = ('id', 'str_field')

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                str_field = CharField(required=False)
        """)

        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_meta_exclude(self):
        """
        Serializer should respect Meta.exclude
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel
                exclude = ('decimal_field', 'custom_field')
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                str_field = CharField(required=False)
                url_field = URLField(required=False)
                email_field = EmailField(required=False)
                int_field = IntegerField(required=False)
                long_field = IntegerField(required=False)
                float_field = FloatField(required=False)
                boolean_field = BooleanField(required=False)
                nullboolean_field = NullBooleanField(required=False)
                date_field = DateTimeField(required=False)
                complexdate_field = DateTimeField(required=False)
                uuid_field = UUIDField(required=False)
                id_field = ObjectIdField(required=False)
        """)

        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_field_options(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = FieldOptionsModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                required_field = IntegerField(required=True)
                null_field = IntegerField(allow_null=True, required=False)
                choices_field = ChoiceField(choices=(('red', 'Red'), ('blue', 'Blue'), ('green', 'Green')), required=False)
                length_limit_field = CharField(max_length=12, min_length=3, required=False)
                value_limit_field = IntegerField(max_value=12, min_value=3, required=False)
                decimal_field = DecimalField(decimal_places=4, max_digits=8, max_value=9999, required=False)
        """)
        # if six.PY2:
        #     # This particular case is too awkward to resolve fully across
        #     # both py2 and py3.
        #     expected = expected.replace(
        #         "('red', 'Red'), ('blue', 'Blue'), ('green', 'Green')",
        #         "(u'red', u'Red'), (u'blue', u'Blue'), (u'green', u'Green')"
        #     )
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_method_field(self):
        """
        Properties and methods on the model should be allowed as `Meta.fields`
        values, and should map to `ReadOnlyField`.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel
                fields = ('id', 'method')

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                method = ReadOnlyField()
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_fields(self):
        """
        Both `pk` and the actual primary key name are valid in `Meta.fields`.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = AutoFieldModel
                fields = ('pk', 'auto_field')

        expected = dedent("""
            TestSerializer():
                pk = IntegerField(read_only=True)
                auto_field = IntegerField(read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_id_field(self):
        """
        The autocreated id field should be mapped properly
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = OneFieldModel
                fields = ('id',)

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_extra_field_kwargs(self):
        """
        Ensure `extra_kwargs` are passed to generated fields.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel
                fields = ('id', 'str_field')
                extra_kwargs = {'str_field': {'default': 'extra'}}

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                str_field = CharField(default='extra')
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_invalid_field(self):
        """
        Field names that do not map to a model field or relationship should
        raise a configuration errror.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel
                fields = ('id', 'invalid')

        with self.assertRaises(ImproperlyConfigured) as excinfo:
            TestSerializer().fields
        expected = 'Field name `invalid` is not valid for model `RegularModel`.'
        assert str(excinfo.exception) == expected

    def test_missing_field(self):
        """
        Fields that have been declared on the serializer class must be included
        in the `Meta.fields` if it exists.
        """
        class TestSerializer(DocumentSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularModel
                fields = ('id',)

        with self.assertRaises(AssertionError) as excinfo:
            TestSerializer().fields
        expected = (
            "The field 'missing' was declared on serializer TestSerializer, "
            "but has not been included in the 'fields' option."
        )
        assert str(excinfo.exception) == expected

    def test_missing_superclass_field_not_included(self):
        """
        Fields that have been declared on a parent of the serializer class may
        be excluded from the `Meta.fields` option.
        """
        class TestSerializer(DocumentSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularModel

        class ChildSerializer(TestSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularModel
                fields = ('id',)

        ChildSerializer().fields

    def test_missing_superclass_field_excluded(self):
        """
        Fields that have been declared on a parent of the serializer class may
        be excluded from the `Meta.fields` option.
        """
        class TestSerializer(DocumentSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularModel

        class ChildSerializer(TestSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularModel
                exclude = ('missing', )

        ChildSerializer().fields

    def test_choices_with_nonstandard_args(self):
        class TestSerializer(DocumentSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = ComplexChoicesModel

        TestSerializer().fields

    def test_fields_and_exclude_behavior(self):
        class ImplicitFieldsSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel

        class ExplicitFieldsSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel
                fields = '__all__'

        implicit = ImplicitFieldsSerializer()
        explicit = ExplicitFieldsSerializer()

        assert implicit.data == explicit.data


class TestIntegration(TestCase):
    maxDiff = 0

    def tearDown(self):
        RegularModel.drop_collection()

    def test_retrival(self):
        instance = RegularModel.objects.create(
            str_field="str",
            url_field="http://qwe.qw/",
            email_field="qwe@qwe.qw",
            int_field=42,
            long_field=9223372036854775807,
            float_field=42e-10,
            boolean_field=True,
            nullboolean_field=None,
            date_field=datetime(2015, 11, 14, 6, 13, 14, 123000),
            complexdate_field=datetime(2015, 11, 14, 6, 13, 14, 123456),
            uuid_field=UUID("36195645-d9d8-4c86-bd88-29143cdb7ad4"),
            id_field=ObjectId("56467a4ba21aab16872f5867"),
            decimal_field=Decimal(1) / Decimal(3)
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'str_field': "str",
            'url_field': "http://qwe.qw/",
            'email_field': "qwe@qwe.qw",
            'int_field': 42,
            'long_field': 9223372036854775807,
            'float_field': 42e-10,
            'boolean_field': True,
            'nullboolean_field': None,
            'date_field': "2015-11-14T06:13:14.123000",
            'complexdate_field': "2015-11-14T06:13:14.123456",
            'uuid_field': "36195645-d9d8-4c86-bd88-29143cdb7ad4",
            'id_field': "56467a4ba21aab16872f5867",
            'decimal_field': "0.33",  # default DRF rounding
            'custom_field': None
        }
        assert serializer.data == expected
        # self.assertEqual(serializer.data, expected)

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel

        data = {
            'str_field': "str",
            'url_field': "http://qwe.qw/",
            'email_field': "qwe@qwe.qw",
            'int_field': 42,
            'long_field': 9223372036854775807,
            'float_field': 42e-10,
            'boolean_field': True,
            'nullboolean_field': None,
            'date_field': "2015-11-14T06:13:14.123000",
            'complexdate_field': "2015-11-14T06:13:14.123456",
            'uuid_field': "36195645-d9d8-4c86-bd88-29143cdb7ad4",
            'id_field': "56467a4ba21aab16872f5867",
            'decimal_field': "0.33",
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.str_field == "str"
        assert instance.url_field == "http://qwe.qw/"
        assert instance.email_field == "qwe@qwe.qw"
        assert instance.int_field == 42
        assert instance.long_field == 9223372036854775807
        assert instance.float_field == 42e-10
        assert instance.boolean_field
        assert instance.nullboolean_field is None
        assert instance.date_field == datetime(2015, 11, 14, 6, 13, 14, 123000)
        assert instance.complexdate_field == datetime(2015, 11, 14, 6, 13, 14, 123456)
        assert instance.uuid_field == UUID("36195645-d9d8-4c86-bd88-29143cdb7ad4")
        assert instance.id_field == ObjectId("56467a4ba21aab16872f5867")
        assert instance.decimal_field == Decimal("0.33")

        expected = {
            'id': str(instance.id),
            'str_field': "str",
            'url_field': "http://qwe.qw/",
            'email_field': "qwe@qwe.qw",
            'int_field': 42,
            'long_field': 9223372036854775807,
            'float_field': 42e-10,
            'boolean_field': True,
            'nullboolean_field': None,
            'date_field': "2015-11-14T06:13:14.123000",
            'complexdate_field': "2015-11-14T06:13:14.123456",
            'uuid_field': "36195645-d9d8-4c86-bd88-29143cdb7ad4",
            'id_field': "56467a4ba21aab16872f5867",
            'decimal_field': "0.33",
            'custom_field': None
        }
        assert serializer.data == expected
        # self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = RegularModel.objects.create(
            str_field="str",
            url_field="http://qwe.qw/",
            email_field="qwe@qwe.qw",
            int_field=42,
            long_field=9223372036854775807,
            float_field=42e-10,
            boolean_field=True,
            nullboolean_field=None,
            date_field=datetime(2015, 11, 14, 6, 13, 14, 123000),
            complexdate_field=datetime(2015, 11, 14, 6, 13, 14, 123456),
            uuid_field=UUID("36195645-d9d8-4c86-bd88-29143cdb7ad4"),
            id_field=ObjectId("56467a4ba21aab16872f5867"),
            decimal_field=Decimal(1) / Decimal(3)
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularModel

        data = {
            'str_field': "str1",
            'url_field': "http://qwe1.qw/",
            'email_field': "qwe1@qwe.qw",
            'int_field': 41,
            'long_field': 9223372036854775801,
            'float_field': 41e-10,
            'boolean_field': False,
            'nullboolean_field': True,
            'date_field': "2015-11-14T06:13:14.121000",
            'complexdate_field': "2015-11-14T06:13:14.123451",
            'uuid_field': "36195645-d9d8-4c86-bd88-29143cdb7ad1",
            'id_field': "56467a4ba21aab16872f5861",
            'decimal_field': "0.31",
        }

        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.str_field == "str1"
        assert instance.url_field == "http://qwe1.qw/"
        assert instance.email_field == "qwe1@qwe.qw"
        assert instance.int_field == 41
        assert instance.long_field == 9223372036854775801
        assert instance.float_field == 41e-10
        assert not instance.boolean_field
        assert instance.nullboolean_field
        assert instance.date_field == datetime(2015, 11, 14, 6, 13, 14, 121000)
        assert instance.complexdate_field == datetime(2015, 11, 14, 6, 13, 14, 123451)
        assert instance.uuid_field == UUID("36195645-d9d8-4c86-bd88-29143cdb7ad1")
        assert instance.id_field == ObjectId("56467a4ba21aab16872f5861")
        assert instance.decimal_field == Decimal("0.31")

        expected = {
            'id': str(instance.id),
            'str_field': "str1",
            'url_field': "http://qwe1.qw/",
            'email_field': "qwe1@qwe.qw",
            'int_field': 41,
            'long_field': 9223372036854775801,
            'float_field': 41e-10,
            'boolean_field': False,
            'nullboolean_field': True,
            'date_field': "2015-11-14T06:13:14.121000",
            'complexdate_field': "2015-11-14T06:13:14.123451",
            'uuid_field': "36195645-d9d8-4c86-bd88-29143cdb7ad1",
            'id_field': "56467a4ba21aab16872f5861",
            'decimal_field': "0.31",
            'custom_field': None
        }
        self.assertEqual(serializer.data, expected)
