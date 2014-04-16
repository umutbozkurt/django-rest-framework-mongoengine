from django.conf.urls import patterns, include, url
from SampleApp import views
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/$', views.UserList.as_view()),
    url(r'^blogs/$', views.BlogList.as_view()),
    url(r'^posts/$', views.PostList.as_view()),
    url(r'^comments/$', views.CommentList.as_view()),
)
