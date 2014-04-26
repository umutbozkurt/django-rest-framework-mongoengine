mongoengine-model-serializer
======================
 
MongoEngine Model Serializer for **Django Rest Framework**
 
0xe801 This serializer is an extension to ***Model Serializer***.
`MongoEngine Model Serializer` is pretty easy to use if you are familiar with DRF.
 
> <i class="icon-right-open"></i>**MongoEngine Model Serializer Provides:**
> 
>  - Serializing
>  - Embedding
>  - Referencing
>  - Validating
>
> MongoEngine Documents
 
----------
<i class="icon-wrench"></i>Usage
---------
Write ***class meta*** as usual and you're done!
```
class CommentSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Comment
        depth = 2
        related_model_validations = {'owner': User, 'post': Post}
        exclude = ('isApproved',)
```
 
----------
<i class="icon-download"></i>Requirements
---------
 
 - MongoEngine
 - Django Rest Framework
 
---------
<i class="icon-cog"></i> Setup
---------
**No additional configuration/setup needed!**
