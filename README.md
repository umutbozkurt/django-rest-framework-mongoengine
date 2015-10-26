Django Rest Framework Mongoengine
===============================

***Mongoengine*** support for ***Django Rest Framework***.

# DRF 3
Starting from `version 2.0`, this package will be developed using `DRF 3.0` and higher. 

# DRF 2
If you want to use `DRFME` with `DRF 2`, you should `version 1.*`. Development will be continued on `drf_2_support` branch.

## Documentation
See full documentation [here](https://pythonhosted.org/django-rest-framework-mongoengine/)
### DocumentSerializer
`DocumentSerializer` works just like as `DRF Model Serializer`. Your model fields are converted to relevant serializer fields automatically. If you want custom behavior, you can use `nested serializers`.
```Python
from rest_framework_mongoengine.serializers import DocumentSerializer

class BlogSerializer(DocumentSerializer):
    class Meta:
        model = Blog
        fields = ('id', 'author', 'name', 'date_created')
```
### DynamicDocumentSerializer
A `DocumentSerializer` for dynamic documents.
### EmbeddedDocumentSerializer
`EmbeddedDocumentSerializer` is used to customize `EmbeddedDocument` behavior, and make `validations` accurately. It is mentioned extensively on the [documentation](https://pythonhosted.org/django-rest-framework-mongoengine/serializers/#embeddeddocumentserializer)
### Generic Views
`Generic Views` are named exactly the same as `DRF Generic Views`. 

Just make sure you are using `DRFME Generics`.

`from rest_framework_mongoengine import generics`

## Installation
`pip install django-rest-framework-mongoengine`

**Note:** You might consider using a specific version.

***For clarity:***
- DRF2 support: `pip install "django-rest-framework-mongoengine<2.0"`
- DRF3 support: `pip install "django-rest-framework-mongoengine>=2.0"`


Don't forget to add the package to installed apps.
```Python
INSTALLED_APPS = (
    ...
    'rest_framework_mongoengine',
)
```

## Maintainers

@Jcbobo88

@qwiglydee

Feel free to mail me if you consider being a maintainer.
