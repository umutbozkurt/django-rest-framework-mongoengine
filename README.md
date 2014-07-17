Mongoengine Model Serializer
======================

MongoEngine ***Model Serializer*** for **Django Rest Framework**.

-----------------
Usage
--------
```
# model
class Blog(Document):
    owner = ReferenceField(User)
    title = StringField()
    extensions = ListField(EmbeddedDocument(BlogExtension))
    tags = ListField(StringField())
    approved = BooleanField()

# serializer
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
