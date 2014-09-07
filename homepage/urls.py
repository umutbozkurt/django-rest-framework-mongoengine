from django.conf.urls import *
from django.conf import settings


urlpatterns = patterns('homepage.views',
    url(r'^$', 'home',      name="home"),
)
