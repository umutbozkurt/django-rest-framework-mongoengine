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

Since Django `get_object_or_404()` shortcut catches only Django ORM DoesNotExist exception and mongoengine has similar, but separatec exceptions, we should replace `get_object_or_404()` usage with try..catch block.

For history purposes: there was `get_document_or_404` shortcut. But since 0.10 mongoengine has dropped Django helpers support.