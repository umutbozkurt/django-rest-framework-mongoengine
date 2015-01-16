from django.conf.urls import patterns, include, url
from SampleApp import views
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/$', views.UserList.as_view()),
    url(r'^users/(?P<id>[\w]{24})/$', views.UserDetails.as_view()),
    url(r'^blogs/$', views.BlogList.as_view()),
    url(r'^blogs/(?P<id>[\w]{24})/$', views.BlogDetails.as_view()),
    url(r'^posts/$', views.PostList.as_view()),
    url(r'^posts/(?P<id>[\w]{24})/$', views.PostDetails.as_view()),
    url(r'^comments/$', views.CommentList.as_view()),
    url(r'^comments/(?P<id>[\w]{24})/$', views.CommentDetails.as_view()),
)
