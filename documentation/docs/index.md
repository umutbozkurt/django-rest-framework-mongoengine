# Django Rest Framework Mongoengine

Source code on [github](http://github.com/umutbozkurt/django-rest-framework-mongoengine).

DRF version 3 support will be distributed under version 2.* and it will be developed on `master` branch. DRF 2 development branch is moved to `drf_2_support`.

This documentation is for version 2. You can find documentation for older versions (that support DRF 2) here-> [placeholder].

## Changelog
***version 2.0***

* Migrated to DRF 3
* Old `MongoEngineModelSerializer` is now `DocumentSerializer`.
* You can use nested serializers now, just like documented on DRF3 [placeholder].
* New `EmbeddedDocumentSerializer` for `EmbeddedDocument`.
* New `ObjectIdField`.
* Old `MongoDocumentField` is now `DocumentField`
* Generic views refactor
