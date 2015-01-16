from models import *
from rest_framework import serializers as drf_serializer
from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine.validators import UniqueValidator


class UserSerializer(DocumentSerializer):
    username = drf_serializer.CharField(validators=[UniqueValidator(User.objects.all())])

    class Meta:
        model = User
        depth = 2


class BlogSerializer(DocumentSerializer):
    class Meta:
        model = Blog
        depth = 3


class PostSerializer(DocumentSerializer):
    class Meta:
        model = Post


class CommentSerializer(DocumentSerializer):
    class Meta:
        model = Comment
        exclude = ('isApproved',)