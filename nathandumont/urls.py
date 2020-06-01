from django.conf.urls import include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from blog.feeds import LatestEntriesFeed
admin.autodiscover()

from blog.views import home, section, tagged_posts, legacy_node, special_page

urlpatterns = [
    # Examples:
    # url(r'^$', 'nathandumont.views.home', name='home'),
    # url(r'^nathandumont/', include('nathandumont.foo.urls')),
    url(r'^$', home, name='home'),
    url(r'rss\.xml$', LatestEntriesFeed()),
    url(r'^page/(?P<offset>\d+)/?$', home, name='home'),
    url(r'^section/(?P<section>[-\w]+)/?$', section, name='section'),
    url(r'^tag/(?P<tag_name>[-\w]+)/?$', tagged_posts, name='tagged_posts'),
    url(r'^tag/(?P<tag_name>[-\w]+)/page/(?P<offset>\d+)/?$', tagged_posts, name='tagged_posts'),
    url(r'^section/(?P<section>[-\w]+)/page/(?P<offset>\d+)/?$', section, name='section'),
    url(r'^blog/', include('blog.urls')),
    url(r'^node/(?P<nid>\d+)/?$', legacy_node, name='legacy-node'),
    url(r'^author/?$', special_page, {'slug': 'author'}, name='author'),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
]

if settings.BLOG_GALLERY:
    from blog.views import gallery_index, gallery
    extra_patterns = [
        url(r'^gallery/?$', gallery_index, name='gallery-index'),
        url(r'^gallery/(?P<slug>[-\w]+)/?$', gallery, name='gallery'),
    ]
    
    urlpatterns += extra_patterns
