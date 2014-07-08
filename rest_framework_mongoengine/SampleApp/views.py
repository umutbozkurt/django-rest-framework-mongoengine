from rest_framework_mongoengine.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from serializers import *


class BlogList(ListCreateAPIView):
    serializer_class = BlogSerializer
    queryset = Blog.objects.all()


class BlogDetails(RetrieveUpdateDestroyAPIView):
    serializer_class = BlogSerializer
    queryset = Blog.objects.all()


class UserList(ListCreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()


class UserDetails(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()


class PostList(ListCreateAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.all()


class PostDetails(RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.all()


class CommentList(ListCreateAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()


class CommentDetails(RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()