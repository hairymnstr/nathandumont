from blog.models import Post, Figure, LegacyNode, Attachment, Comment, Section, Gallery, Tag, PostTag, ForeignNode
from django.contrib import admin
from django.conf.urls import patterns, url
from django.template import RequestContext, loader
import re, httplib, urlparse
from django.http import HttpResponse
from functools import update_wrapper
from django.shortcuts import get_object_or_404
from tidylib import tidy_document

def check_url(url):
    if(url[0] == '/'):
        conn = httplib.HTTPConnection("nathandumont.home")
        conn.request("HEAD", url)
        res = conn.getresponse()
    else:
        oldloc = urlparse.urlparse(url)
        if(oldloc.scheme == "http"):
            conn = httplib.HTTPConnection(oldloc.netloc)
        elif(oldloc.scheme == "https"):
            conn = httplib.HTTPSConnection(oldloc.netloc)
        else:
            return url, -1, "unhandled scheme", ""
        rqurl = oldloc.path
        if(oldloc.query != ""):
            rqurl += "?"
            rqurl += oldloc.query
        if(oldloc.fragment != ""):
            rqurl += "#"
            rqurl += oldloc.fragment
        try:
            conn.request("GET", rqurl)
            res = conn.getresponse()
        except:
            res = None
        
    if(res):
        code = res.status
        if(code == 301):
            style = 'style="background: #fff551"'
            loc = res.getheader('location')
            new_loc = urlparse.urlparse(loc)
            if(new_loc.netloc == "nathandumont.home"):
                extra = new_loc.path
            else:
                extra = loc
        elif(code == 200):
            style = 'style="background: #75ff5e"'
            extra = ""
        elif(code == 404):
            style = 'style="background: #ff5e5e"'
            extra = ""
        else:
            style = ""
            extra = ""
    else:
        style = ""
        extra = ""
        code = -1

    return url, code, extra, style
    
class LegacyNodeInline(admin.StackedInline):
    model = LegacyNode
    max_num = 1
  
class CommentInline(admin.StackedInline):
    model = Comment
  
class AttachmentInline(admin.TabularInline):
    model=Attachment

class FigureInline(admin.TabularInline):
    model = Figure
    fields = ('img', 'title', 'caption', 'label')

class FigureAdmin(admin.ModelAdmin):
    model = Figure
    readonly_fields = ('preview_tag',)
    fields = ('img', ('thumbnail', 'preview_tag'), 'title', 'caption', 'label', 'gallery')
    ordering = ('label',)
    
class PostAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'classes': ('monospace',),
            'fields': (('title', 'slug'), 'source', 'section', 'last_modified', 'published', 'special')
        }),
    )
    inlines = [AttachmentInline, LegacyNodeInline]
    list_display = ('title', 'last_modified', 'section', 'published', 'special')
    readonly_fields = ('slug',)
    ordering = ('-last_modified',)
    model = Post
    
    def get_urls(self):
        urls = super(PostAdmin, self).get_urls()

        my_urls = patterns('',
            url(r'^link_status/$', self.admin_site.admin_view(self.link_status)),
            url(r'^validation/(?P<post_id>\d+)/$', self.admin_site.admin_view(self.validation))
        )
        return my_urls + urls
    
    def link_status(self, request, *args, **kwargs):
        re_img = re.compile(r'<img[^<>]*?src=["' r"']([^'" r'"' r"]+)['" r'"][^<>]*/>')
        re_a = re.compile(r'<a[^<>]*?href=["' r"']([^'" r'"]+)["' r"'][^<>]*>")
        pages = []
        for post in Post.objects.all():
            page = {}
            page['title'] = post.title
            page['links'] = []
            
            for a in re_a.finditer(post.source):
                print a.groups()
                url, code, extra, style = check_url(a.groups()[0])
                page['links'].append({'url': url, 'code': code, 'extra': extra, 'style': style})
                
            page['images'] = []
            for src in re_img.finditer(post.source):
                url, code, extra, style = check_url(src.groups()[0])
                page['images'].append({'url': url, 'code': code, 'extra': extra, 'style': style})
        
            if(len(page['links']) + len(page['images']) > 0):
                pages.append(page)
        t = loader.get_template('blog/link_status.html')
        c = RequestContext(request, {'pages': pages, 'app_label': 'blog', 'opts': self.model._meta})
  
        return HttpResponse(t.render(c))
        
    def validation(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        document, errors = tidy_document("<!DOCTYPE html><html><head><title>test</title></head><body>" + 
                                  post.rendered + "</body></html>")
        
        t = loader.get_template('blog/verify.html')
        c = RequestContext(request, {'errors': errors, 'opts': self.model._meta, 
                                     'title': post.title, 'app_label': 'blog',
                                     'original': post.title,
                                     'post': post})
        
        return HttpResponse(t.render(c))
        
class GalleryAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'label')
        }),
    )
    inlines = [FigureInline]
  
admin.site.register(Post, PostAdmin)
admin.site.register(Figure, FigureAdmin)
admin.site.register(Section)
admin.site.register(Gallery, GalleryAdmin)
admin.site.register(Tag)
admin.site.register(PostTag)
admin.site.register(Attachment)
admin.site.register(LegacyNode)
admin.site.register(ForeignNode)
admin.site.register(Comment)
