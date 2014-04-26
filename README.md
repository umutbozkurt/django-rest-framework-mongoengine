mongoengine-model-serializer
======================
 
MongoEngine Model Serializer for **Django Rest Framework**
 
This serializer is an extension to ***Model Serializer***.
`MongoEngine Model Serializer` is pretty easy to use if you are familiar with DRF.
 
> <i class="icon-right-open"></i>**MongoEngine Model Serializer Provides:**
> 
>  - Serializing
>  - Embedding
>  - Referencing
>  - Validating
>
> MongoEngine Documents

<i class="icon-cog"></i> Setup
---------
``` pip install django-rest-framework-mongoengine```

<i class="icon-wrench"></i>Usage
---------

serializers.py
``` 
from rest_framework_mongoengine import mongoengine_serializer

class CommentSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Comment
        depth = 2
        related_model_validations = {'owner': User, 'post': Post}
        exclude = ('isApproved',)
```
models.py
``` 
class Comment(Document):
    post = ReferenceField(Post)
    owner = ReferenceField(User)
    text = StringField(max_length=140)
    isApproved = BooleanField(default=False)
```
Mongoengine Model Serializer will **reference** or **embed** Post/User Documents regarding CommentSerializer's **depth**.

<i class="icon-download"></i>Requirements
---------
 
 - MongoEngine
 - Django Rest Framework
 

