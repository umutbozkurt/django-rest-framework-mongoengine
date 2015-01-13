# DocumentSerializer

DocumentSerializer is a subclass of DRF's [ModelSerializer](http://www.django-rest-framework.org/api-guide/serializers/#modelserializer).

If you are not familiar with DRF ModelSerializer, you should first visit it's documentation page.

For basic implementation, DocumentSerializer works similar to ModelSerializer.

## Sample Implementation

***models.py***

```Python
class User(Document):
    username = StringField(max_length=30)
    email = EmailField(max_length=30)
    friends = ListField(ReferenceField('self'))
    extra = DictField()

class BlogExtension(EmbeddedDocument):
    further_read = StringField(required=True)
    references = ListField(StringField())

class Blog(DynamicDocument):
    owner = ReferenceField(User)
    title = StringField(max_length=30)
    tags = ListField(StringField())

class Comment(EmbeddedDocument):
    author = ReferenceField(User)
    text = StringField(max_length=140)
    is_approved = BooleanField(default=False)

class Post(Document):
    author = ReferenceField(User)
    blog = ReferenceField(Blog)
    text = StringField()
    comments = ListField(EmbeddedDocumentField(Comment))
    extension = EmbeddedDocumentField(BlogExtension)
```

***serializers.py***

```Python
class PostSerializer(DocumentSerializer):
    class Meta:
        model = Post
        depth = 2
```

Post document is serialized to:

```JSON
{
    "id": "54b453dd03c9804f7fbd822f",
    "blog": {
        "id": "5452025903c980036a7221f1",
        "owner": "5452020703c980036a7221f0",
        "title": "new blog"
        "tags": [
            "python",
            "django",
            "mongodb"
        ],
    },
    "author": {
        "id": "5452020703c980036a7221f0",
        "username": "John",
        "email": null,
        "friends": [
            "id": "54b188db03c98125076329c4",
            "username": "Tim",
            "email": null,
            "friends": [
                "5452020703c980036a7221f0"
                ]
        ],
        "extra": {"is_verified": true}
    },
    "text": "Yet another new post about MongoDB",
    "comments": [
        {
            "text": "Definitely a good read.",
            "is_approved": true,
            "author": "54b188db03c98025076329c4"
        },
        {
            "text": "Thanks for the post!",
            "is_approved": true,
            "author": "54b188db03c98125076329c4"
        }
    ],
    "extension": {
        "references": [
            "Tom",
            "Mongoengine",
            "DRF"
        ],
        "further_read": "See Tom's post about Mongoengine"
    }
}
```

### Warnings

`DocumentSerializer` can get basic-field's (like `StringField`) kwargs and pass it to serializer for **validation**. But on compound fields like `ListField`, `EmbeddedDocumentField`, there is no kwarg to pass for validation. For example `ListField(User)`, serializer can not know User's fields and their kwargs. If you want that to restrict users and improve validation on compound fields, you should use `nested serializers`.

## Nested Serializers

In many cases, you may want to customize serialization process. You can use nested serializers.

You can use DocumentSerializer for:

- ReferenceField
- ListField

[EmbeddedDocumentSerializer](#embeddeddocumentserializer) for:

- EmbeddedDocumentField

For concerns about ambiguity and complexity about **automatic** nested serialization, Django Rest Framework has decided to NOT to do it. Instead, you can explicitly define your nested-serialization behavior. See [DRF documentation](http://www.django-rest-framework.org/api-guide/serializers/#writable-nested-representations)

For using `DocumentSerializer` as ***nested serializer***, you have to implement it **manually** like documented.

### Sample Implementation

```Python
class ExtensionSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = BlogExtension

class BlogSerializer(DocumentSerializer):
    extension = ExtensionSerializer(many=False)

    class Meta:
    model = Blog

class PostSerializer(DocumentSerializer):
    author = FriendSerializer(many=False)
    comments = CommentSerializer(many=True)
    extension = ExtensionSerializer(many=False)

    class Meta:
        model = Post
        fields = ('id', 'blog', 'author', 'text', 'comments', 'extension')
        depth = 2
```

## EmbeddedDocumentSerializer

Unlike DocumentSerializer, behavior on `EmbeddedDocuments` are not ambiguous.
You dont have to implement when nesting `EmbeddedDocumentSerializer`, it is done automatically for you on the go while (de)serializing.

**Note:**Calling `EmbeddedDocumentSerializer.save()` will raise an exception, because `EmbeddedDocuments` need a `Document` to attach to.

### Warning About EmbeddedDocumentSerializer(many=True)
On DRF 3, when you set serializer with `many=True` kwarg, it automatically converts to `ListSerializer`, which will lead to a nested serializer exception (from DRF). There is a workaround which is supplying `.create()` and/or `.update()` methods.

For example, as you see below, custom `.update()` is provided because CommentSerializer has kwarg `many=True`.

```Python
class CommentSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = Comment

class PostSerializer(DocumentSerializer):
    comments = CommentSerializer(many=True)
    extension = ExtensionSerializer(many=False)

    class Meta:
        model = Post
        fields = ('id', 'blog', 'author', 'text', 'comments', 'extension')
        depth = 2

    def update(self, instance, validated_data):
        comments = validated_data.pop('comments')
        updated_instance = super(PostSerializer, self).update(instance, validated_data)

        for comment_data in comments:
            updated_instance.comments.append(Comment(**comment_data))

        updated_instance.save()
        return updated_instance
```
