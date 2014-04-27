Mongoengine Model Serializer
======================

<i class="icon-info-circled"></i> Introduction
-----------------

MongoEngine Model Serializer for **Django Rest Framework**
 
This serializer is an extension to ***Model Serializer***.

`MongoEngine Model Serializer` is pretty easy to learn and has flexible usage.

-----------------
Documentation
-----------------
See [DOCUMENTATION][1] for more detailed info.

-----------------
<i class="icon-th-list"></i> Features
-----------------

>  - Serializing
>  - Embedding
>  - Referencing
>  - Validating
>
> MongoEngine Documents

-----------------

<i class="icon-download"></i> Setup
---------
### <i class="icon-download-cloud">Pip Installer</i> 
``` pip install django-rest-framework-mongoengine```
### <i class="icon-folder-open">GitHub Releases</i> 
Download from Repo's [releases][2] section.

-----------------
<i class="icon-wrench"></i>Usage
---------
###Embedding and Referencing
``` 
class CommentSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Comment
        depth = 1
        related_model_validations = {'owner': User, 'post': Post}
        exclude = ('isApproved',)
```
####models.py
``` 
class Comment(Document):
    post = ReferenceField(Post)
    owner = ReferenceField(User)
    text = StringField(max_length=140)
    isApproved = BooleanField(default=False)
```
![Sample Output][3]

### <i class="icon-right-big"></i>Validation

#### <i class="icon-angle-right"></i>Reference Field Validation

```
related_model_validations = {'owner': User, 'post': Post}
```

![validation][4]


#### <i class="icon-angle-right"></i> Field Validation

```
class User(Document):
    name = StringField(max_length=50)
    rating = DecimalField(max_digits=2, decimal_places=1)
    username = StringField(max_length=30)
    email = EmailField(max_length=30)
```

![field-validation][5]

-----------------
<i class="icon-attach"></i>Requirements
-----------------
 
 - [MongoEngine][6]
 - [Django Rest Framework][7]
 
-----------------
<i class="icon-doc-text"></i>License
-----------------
See [LICENSE][8]


  [1]: https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/master/DOCUMENTATION.md
  [2]: https://github.com/umutbozkurt/django-rest-framework-mongoengine/releases
  [3]: https://lh4.googleusercontent.com/-Gf_do_QmMHo/U1zTSghmCZI/AAAAAAAAACs/QA5tELHm66I/w511-h382-no/Screen+Shot+2014-04-27+at+12.47.13.png
  [4]: https://lh6.googleusercontent.com/--DFC8tBE1JA/U1zXZJlQ16I/AAAAAAAAADA/uAglm0TdXOk/w464-h103-no/Screen+Shot+2014-04-27+at+13.09.13.png
  [5]: https://lh3.googleusercontent.com/-c9RhYm3RD9s/U1ziBxGx0TI/AAAAAAAAADc/dyRRrIUiAmc/w486-h162-no/Screen+Shot+2014-04-27+at+13.54.34.png
  [6]: http://mongoengine.org/
  [7]: http://www.django-rest-framework.org/
  [8]: https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/master/LICENSE
