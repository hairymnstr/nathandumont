from blog.models import Post, Figure, LegacyNode, Attachment, Comment, Section, Gallery, Tag
from blog.models import PostTag, ForeignNode, PostGroupItem, PostGroup, ExternalGroupItem
from django.contrib import admin
from django.conf.urls import url
from django.template import RequestContext, loader
from django.http import HttpResponse
import re
from tidylib.tidy import Tidy
from functools import update_wrapper
from django.shortcuts import get_object_or_404, render

"""def check_url(url):
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

    return url, code, extra, style"""
    
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

class PostTagInline(admin.TabularInline):
    model = PostTag
    fields = ('tag',)
    
class PostGroupItemInline(admin.TabularInline):
    model = PostGroupItem
    
class ExternalGroupItemInline(admin.TabularInline):
    model = ExternalGroupItem
    
class FigureAdmin(admin.ModelAdmin):
    model = Figure
    readonly_fields = ('preview_tag', 'modified', 'created')
    fields = ('img', ('thumbnail', 'preview_tag'), 'title', 'caption', 'label', ('created', 'modified'), 'gallery')
    ordering = ('-created',)
    list_display = ('title', 'modified', 'created', 'label', 'gallery')
    
class TagAdmin(admin.ModelAdmin):
    model = Tag
    fields = ('text', 'slug', 'legacyId')
    ordering = ('text',)
    list_display = ('text', 'slug')

class PostAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'classes': ('monospace',),
            'fields': (('title', 'slug'), 'source', 'section', 'last_modified', 'published', 'special', 'reviewed')
        }),
    )
    inlines = [AttachmentInline, PostTagInline, LegacyNodeInline]
    list_display = ('title', 'last_modified', 'section', 'published', 'special', 'reviewed')
    readonly_fields = ('slug',)
    ordering = ('-last_modified',)
    model = Post
    
    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            #url(r'^link_status/$', self.admin_site.admin_view(self.link_status)),
            url(r'^(?P<post_id>\d+)/validate/$', self.admin_site.admin_view(self.validation)),
            url(r'^(?P<post_id>\d+)/preview/$', self.admin_site.admin_view(self.preview)),
        ]
        return my_urls + urls
    
    """def link_status(self, request, *args, **kwargs):
        re_img = re.compile(r'<img[^<>]*?src=["' r"']([^'" r'"' r"]+)['" r'"][^<>]*/>')
        re_a = re.compile(r'<a[^<>]*?href=["' r"']([^'" r'"]+)["' r"'][^<>]*>")
        pages = []
        for post in Post.objects.all():
            page = {}
            page['title'] = post.title
            page['links'] = []
            
            for a in re_a.finditer(post.source):
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
  
        return HttpResponse(t.render(c))"""
        
    def validation(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        t = Tidy()
        document, errors = t.tidy_document("<!DOCTYPE html><html><head><title>test</title></head><body>" + 
                                  post.rendered + "</body></html>")
        
        return render(request, 'admin/blog/post/verify.html', {
            'errors': errors, 'opts': self.model._meta, 
            'title': post.title, 'app_label': 'blog',
            'original': post.title,
            'post': post
            })
        
    def preview(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        
        return render(request, "admin/blog/post/preview.html", {
            'post': post,
            'opts': self.model._meta,
            'title': 'Preview for "%s"' % post.title,
            })
            
class GalleryAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'label', 'description', 'gallery_date', 'hidden')
        }),
    )
    inlines = [FigureInline]
    list_display = ('title', 'label', 'hidden')
  
class PostGroupAdmin(admin.ModelAdmin):
    inlines = (PostGroupItemInline, ExternalGroupItemInline)
    readonly_fields = ('slug',)
    
admin.site.register(Post, PostAdmin)
admin.site.register(Figure, FigureAdmin)
admin.site.register(Section)
admin.site.register(Gallery, GalleryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(PostTag)
admin.site.register(Attachment)
admin.site.register(LegacyNode)
admin.site.register(ForeignNode)
admin.site.register(Comment)
admin.site.register(PostGroup, PostGroupAdmin)
