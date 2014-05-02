from models import *
from serializers import MongoEngineModelSerializer


class UserSerializer(MongoEngineModelSerializer):
    class Meta:
        model = User


class BlogSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Blog
        depth = 1
        related_model_validations = {'owner': User}


class PostSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Post
        depth = 1
        related_model_validations = {'author': User, 'blog': Blog}


class CommentSerializer(MongoEngineModelSerializer):
    class Meta:
        model = Comment
        depth = 2
        related_model_validations = {'owner': User, 'post': Post}
        exclude = ('isApproved',)