from mongoengine import *

connect('MySampleDB')

### MongoEngineModelSerializer supports Documents and Reference Fields, for now.


class User(Document):
    name = StringField(max_length=50)
    surname = StringField(max_length=20)
    username = StringField(max_length=30)
    email = EmailField(max_length=30)


class BlogExtension(EmbeddedDocument):
    extra_field = StringField()
    some_other_field = StringField()


class Blog(Document):
    owner = ReferenceField(User)
    title = StringField(max_length=30)
    extension = EmbeddedDocumentField(BlogExtension)
    post_list = ListField(ReferenceField('Post'))


class Post(Document):
    author = ReferenceField(User)
    blog = ReferenceField(Blog)
    text = StringField()


class Comment(Document):
    owner = ReferenceField(User)
    post = ReferenceField(Post)
    text = StringField(max_length=140)
    isApproved = BooleanField(default=False)


