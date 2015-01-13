# Generic Views

Generic views are exactly the same as DRF Generic Views.
Just remember to import and subclass the ones from this package. There can be confusions because all named same.

## Sample Usage
If you are using both DRF and DRFME generic views,

It is good practise to import like

`from rest_framework import generics as drf_generics`
`from rest_framework_mongoengine import generics as drfme_generics`

and use drfme_generics.ListAPIView, drfme_generics.ListCreateAPIView and so on.


## Overriding get_object()

When overriding `get_object()`, remember to user `get_document_or_404()` instead of `get_object_or_404()`

`from mongoengine.django.shortcuts import get_document_or_404`
