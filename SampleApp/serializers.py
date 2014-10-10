from models import *
from rest_framework_mongoengine.serializers import MongoEngineModelSerializer


class UserSerializer(MongoEngineModelSerializer):
    class Meta:
        model = User


class BlogSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Blog
        depth = 3


class PostSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Post


class CommentSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Comment
        exclude = ('isApproved',)