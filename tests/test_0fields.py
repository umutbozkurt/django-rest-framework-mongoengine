from __future__ import unicode_literals

import pytest

from bson import ObjectId

from django.test import TestCase

from rest_framework_mongoengine import fields

from .utils import FieldValues


class TestObjectId(FieldValues, TestCase):
    field = fields.ObjectIdField()
    valid_inputs = {
        ObjectId('56353a4aa21aab2c49d86ebb'): ObjectId('56353a4aa21aab2c49d86ebb'),
        '56353a4aa21aab2c49d86ebb': ObjectId('56353a4aa21aab2c49d86ebb')
    }
    invalid_inputs = {
        123: ['"123" is not a valid ObjectId'],
        'xxx': ['"xxx" is not a valid ObjectId']
    }
    outputs = {
        ObjectId('56353a4aa21aab2c49d86ebb'): '56353a4aa21aab2c49d86ebb',
        '56353a4aa21aab2c49d86ebb': '56353a4aa21aab2c49d86ebb'
    }
