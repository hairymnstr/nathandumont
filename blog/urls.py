from django.conf.urls import url
from blog.views import blog_page

urlpatterns = [
  url(r'^(?P<slug>[-\w]+)/?$', blog_page, name='post-view'),
]
