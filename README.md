Django Rest Framework Mongoengine
=================================

[![Join the chat at https://gitter.im/BurkovBA/django-rest-framework-mongoengine](https://badges.gitter.im/BurkovBA/django-rest-framework-mongoengine.svg)](https://gitter.im/BurkovBA/django-rest-framework-mongoengine?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Build Status](https://travis-ci.org/BurkovBA/django-rest-framework-mongoengine.svg?branch=master)](https://travis-ci.org/BurkovBA/django-rest-framework-mongoengine)
[![codecov](https://codecov.io/gh/BurkovBA/django-rest-framework-mongoengine/branch/master/graph/badge.svg)](https://codecov.io/gh/BurkovBA/django-rest-framework-mongoengine)

The package provides [mongoengine](mongoengine.org) support for [django-rest-framework](https://github.com/tomchristie/django-rest-framework)

## Documentation

For full documentation, usage and examples refer to [DRF manuals](http://www.django-rest-framework.org/). 

The features and differences of this package are described in [API documentation](http://umutbozkurt.github.io/django-rest-framework-mongoengine/) 

## Requirements

* Django == 1.*
* djangorestframework == 3.*
* mongoengine == 0.10.* | 0.9.*
* blinker == 1.* (for mongoengine referencefields to work)
* With mongoengine 0.10: pymongo == 3.*
* With mongoengine 0.9: pymongo == 2.*

## Installation

### from pypi

`pip install django-rest-framework-mongoengine`

### from github

* download [some release from github](https://github.com/umutbozkurt/django-rest-framework-mongoengine/releases), unpack somewhere.
* copy subdir `unpacked_path/rest_framework_mongoengine` into your django project or inside python path
* or, install using `pip unpacked_path`

### do not use git clone!

It may contain non-working code. Before using it, run tests to ensure the code is working.  

## Usage

### Include the packages in Django settings.

```Python
INSTALLED_APPS = (
    ...
    'rest_framework'
    'rest_framework_mongoengine',
    ...
)
```

### Import modules

Use corresponding classes from this package in place of original DRF stuff. Refer to API documentation.

## Testing

If you discover something does not work on the DRFM side, the best way to ensure that and report an issue - is to write a test case, with minimal code that fails. 
You may use [this template](https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/master/tests/test_0dumb.py) to create your case.

If you have something (Django, DRF, mongoengine) at a version, not mentioned in release notes, you better run all the tests in your environment to ensure the DRFM is compatible with that version.

For tests to work, you need pytest in your environment. 

To run all the tests:

```./runtests.py --fast```

To run tests from separate file, class or method:

```./runtests.py --fast test_name```

## Releases

### Current release 

Intended to match DRF API. The major and minor version number matches supported version of DRF.
Note: this release is incompatible with all previous.

### Old releases

Releases 2.x were not well compatible with DRF and mongoengine. Current code is mostly refactored and reimplemented.

### Ancient releases

Releases 1.x were developed to work with `DRF 2`. This branch is no longer supported. 
Documentation available [here](https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/drf_2_support/README.md)

## Maintainers

@qwiglydee

Feel free to mail me if you consider being a maintainer.
