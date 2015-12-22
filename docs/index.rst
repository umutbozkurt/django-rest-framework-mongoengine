The Django Rest Framework Mongoengine
=====================================

The package provides support for mongoengine_  to work with `Django Rest Framework`_ 
Provided classes are mostly reproduce corresponding DRF classes. The usage of them is the same as in upstream. But the implemenation may have differences and features, and some code relying on DRF internals may not work propery.

At version 3.x the modules are refactored to closer match upstream API and behaviour. Major and minor versions intended to match supported version of DRF. 

Older versions are not supported anymore. `Older documentation is available here`_.

Sources are available at https://github.com/umutbozkurt/django-rest-framework-mongoengine

.. _mongoengine: http://mongoengine.org/
.. _Django Rest Framework: http://www.django-rest-framework.org/
.. _Older documentation is available here: https://pythonhosted.org/django-rest-framework-mongoengine/

.. toctree::
   :maxdepth: 3

   serializers
   fields
   validators           
   generics
   viewsets
   routers
