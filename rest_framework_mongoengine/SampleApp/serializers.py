from models import *
from rest_framework_mongoengine.serializers import MongoEngineModelSerializer


class UserSerializer(MongoEngineModelSerializer):
    class Meta:
        model = User


class BlogSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Blog
        related_model_validations = {'owner': User}


class PostSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Post
        related_model_validations = {'author': User, 'blog': Blog}


class CommentSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Comment
        related_model_validations = {'owner': User, 'post': Post}
        exclude = ('isApproved',)