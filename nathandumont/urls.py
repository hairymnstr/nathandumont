from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'nathandumont.views.home', name='home'),
    # url(r'^nathandumont/', include('nathandumont.foo.urls')),
    url(r'^blog/', include('blog.urls')),
    url(r'^node/(?P<nid>\d+)', 'blog.views.legacy_node'),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
