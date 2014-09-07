Mongoengine Model Serializer
======================

***Model Serializer*** that supports ***MongoEngine***, for ***Django Rest Framework***.

-----------------
Usage
--------
```python
# model
class Blog(Document):
    owner = ReferenceField(User)
    title = StringField()
    extensions = ListField(EmbeddedDocument(BlogExtension))
    tags = ListField(StringField())
    approved = BooleanField()

# serializer
from rest_framework_mongoengine.serializers import MongoEngineModelSerializer

class BlogSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Blog
        depth = 2
        exclude = ('approved', )
```
**Notes:** 

 - MongoEngine Model Serializer also supports  ***DynamicDocument***. 
 - `Depth` is optional and defaults to 5. It is used for ***ReferenceField*** & ***ListField***.

Sample Output
---------

![Sample Output][1]

-----------------
Install
---------
``` pip install django-rest-framework-mongoengine```

-----------------
Install as package
-----------------
You can use this library as a package to your project:

Step 1: Installing required files
``` pip install -r requirements.txt```
Step 2: make sure you're having a mongodb running locally:
```/bin/mongod --dbpath [path_to_data/db/]```
Step 3: Create users and table in dbsqlite and django admin:
``` python manage.py syncdb```
Step 4: Run the SampleApp demo:
``` python manage.py runserver```

Then run http://localhost:8000/ on your favorite browser to test the interface

-----------------
Requirements
-----------------
 
 - [MongoEngine][2]
 - [Django Rest Framework][3]
 
-----------------
License
-----------------
See [LICENSE][4]


  [1]: https://lh6.googleusercontent.com/-vv4lo9TXrgA/U8gfzWS3tzI/AAAAAAAAAE0/Xqum8YjrSqk/w570-h521-no/Screen+Shot+2014-07-17+at+22.06.43.png
  [2]: http://mongoengine.org/
  [3]: http://www.django-rest-framework.org/
  [4]: https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/master/LICENSE
