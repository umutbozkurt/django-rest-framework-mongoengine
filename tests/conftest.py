def pytest_configure():
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL='/static/',
        ROOT_URLCONF='tests.urls',
        TEMPLATE_LOADERS=(),
        MIDDLEWARE_CLASSES=(),
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'rest_framework',
            'rest_framework_mongoengine',
            'tests',
        ),
        AUTHENTICATION_BACKENDS=(),
        PASSWORD_HASHERS=(),
    )

    from mongoengine import connect
    connect('test')

    try:
        import django
        django.setup()
    except AttributeError:
        pass
