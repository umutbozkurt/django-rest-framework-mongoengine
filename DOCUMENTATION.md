Mongoengine Model Serializer
======================

<i class="icon-info-circled"></i> Introduction
-----------------

MongoEngine Model Serializer for **Django Rest Framework**
 
This serializer is an extension to ***Model Serializer***.

`MongoEngine Model Serializer` is pretty easy to learn and has flexible usage.
 
<i class="icon-sitemap"></i> Table of Contents
-----------------

[TOC]

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
Download from Repo's [releases][1] section.

-----------------
<i class="icon-wrench"></i>Usage
---------
###Embedding and Referencing
####serializers.py

``` 
from rest_framework_mongoengine import mongoengine_serializer

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
>**Hint:** Mongoengine Model Serializer will **reference** or **embed**  Post/User Documents regarding CommentSerializer's **depth**.
####<i class="icon-code"></i>Sample Output
CommentSerializer **embedded** *'owner'* and *'post'* Documents
and **referenced** *'blog'* and *'author'* inside 'post' Document because depth is **1**
![Sample Output][2]

### <i class="icon-right-big"></i>Validation

#### <i class="icon-angle-right"></i>Reference Field Validation

Mongoengine Model Serializer has built-in Reference Field validation.
Just one extra line of code in ***Serializer Class***. 

```
related_model_validations = {'owner': User, 'post': Post}
```

##### Sample Output

![validation][3]


#### <i class="icon-angle-right"></i> Field Validation
Specify you validations on ***models.py***, just like regular Model Serializer.

```
class User(Document):
    name = StringField(max_length=50)
    rating = DecimalField(max_digits=2, decimal_places=1)
    username = StringField(max_length=30)
    email = EmailField(max_length=30)
```

##### Sample Output

![field-validation][4]

-----------------
<i class="icon-attach"></i>Requirements
-----------------
 
 - [MongoEngine][5]
 - [Django Rest Framework][6]
 
-----------------
<i class="icon-doc-text"></i>License
-----------------
See [LICENSE][7]


  [1]: https://github.com/umutbozkurt/django-rest-framework-mongoengine/releases
  [2]: https://lh4.googleusercontent.com/-Gf_do_QmMHo/U1zTSghmCZI/AAAAAAAAACs/QA5tELHm66I/w511-h382-no/Screen+Shot+2014-04-27+at+12.47.13.png
  [3]: https://lh6.googleusercontent.com/--DFC8tBE1JA/U1zXZJlQ16I/AAAAAAAAADA/uAglm0TdXOk/w464-h103-no/Screen+Shot+2014-04-27+at+13.09.13.png
  [4]: https://lh3.googleusercontent.com/-c9RhYm3RD9s/U1ziBxGx0TI/AAAAAAAAADc/dyRRrIUiAmc/w486-h162-no/Screen+Shot+2014-04-27+at+13.54.34.png
  [5]: http://mongoengine.org/
  [6]: http://www.django-rest-framework.org/
  [7]: https://github.com/umutbozkurt/django-rest-framework-mongoengine/blob/master/LICENSE
