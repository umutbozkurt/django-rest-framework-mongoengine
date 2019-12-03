import os
from setuptools import setup



def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}

setup(
    name='django-rest-framework-mongoengine',
    version='3.4.1',
    description='MongoEngine support for Django Rest Framework.',
    packages=get_packages('rest_framework_mongoengine'),
    package_data=get_package_data('rest_framework_mongoengine'),
    license='see https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/master/LICENSE',
    long_description='see https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/master/README.md',
    url='https://github.com/umutbozkurt/django-rest-framework-mongoengine',
    download_url='https://github.com/umutbozkurt/django-rest-framework-mongoengine/releases/',
    keywords=['mongoengine', 'serializer', 'django rest framework'],
    author='Umut Bozkurt',
    author_email='umutbozkurt92@gmail.com',
    requires=[
        'mongoengine',
        'djangorestframework'
    ],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'License :: OSI Approved :: MIT License',
                 'Natural Language :: English',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 3',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Topic :: Internet',
                 'Topic :: Internet :: WWW/HTTP :: Site Management',
                 'Topic :: Text Processing :: Markup :: HTML',
                 'Intended Audience :: Developers'
                 ],
)
