Fields
======

.. currentmodule:: rest_framework_mongoengine

These are some fields specific to mongoengine, or used internally by the serializers.

The fields that are derived from :class:`fields.DocumentField` are dependend on underlying mongoengine field and used internally by :class:`serializers.DocumentSerializer`. Other fields can be used in ordinary DRF serializer.


GenericField
------------

.. autoclass:: rest_framework_mongoengine.fields.GenericField(**kwargs)
   :show-inheritance:

GeoPointField
-------------

.. autoclass:: rest_framework_mongoengine.fields.GeoPointField(**kwargs)
   :show-inheritance:

GeoJSONField
------------

.. autoclass:: rest_framework_mongoengine.fields.GeoJSONField
   :show-inheritance:

ObjectIdField
-------------

.. autoclass:: rest_framework_mongoengine.fields.ObjectIdField(**kwargs)
   :show-inheritance:

ReferenceField
--------------

.. autoclass:: rest_framework_mongoengine.fields.ReferenceField
   :show-inheritance:

GenericReferenceField
---------------------

.. autoclass:: rest_framework_mongoengine.fields.GenericReferenceField(**kwargs)
   :show-inheritance:

GenericEmbeddedField
--------------------

.. autoclass:: rest_framework_mongoengine.fields.GenericEmbeddedField
   :show-inheritance:

DocumentField
-------------

.. autoclass:: rest_framework_mongoengine.fields.DocumentField
   :show-inheritance:

DynamicField
------------

.. autoclass:: rest_framework_mongoengine.fields.DynamicField
   :show-inheritance:

GenericEmbeddedDocumentField 
----------------------------

.. autoclass:: rest_framework_mongoengine.fields.GenericEmbeddedDocumentField 
   :show-inheritance:

