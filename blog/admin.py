from blog.models import Post, Figure, LegacyNode, Attachment, Comment
from django.contrib import admin

class LegacyNodeInline(admin.StackedInline):
  model = LegacyNode
  max_num = 1
  
class CommentInline(admin.StackedInline):
  model = Comment
  
class AttachmentInline(admin.TabularInline):
  model=Attachment

class PostAdmin(admin.ModelAdmin):
  fields = ('title', 'source', 'published')
  inlines = [AttachmentInline, CommentInline, LegacyNodeInline]

admin.site.register(Post, PostAdmin)
admin.site.register(Figure)
