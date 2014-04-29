from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template import RequestContext, loader
from django.shortcuts import get_object_or_404
from blog.models import Post, LegacyNode, ForeignNode, Attachment, Comment, Section, PostTag
from math import ceil
# Create your views here.

def home(request, offset="1"):
  limit = int(offset) - 1
  posts = Post.objects.filter(published=True, special=False).order_by('-last_modified')[limit*10:(limit+1)*10]
  
  num_posts = Post.objects.filter(published=True, special=False).count()
  
  pages = int(ceil(num_posts / 10.0))
  
  if(limit > 0):
      prev_page = limit
  else:
      prev_page = False
  if(limit < pages-1):
      next_page = limit + 2
  else:
      next_page = False
  
  t = loader.get_template('blog/index.html')
  c = RequestContext(request, {'posts': posts, 'area': 'Home', 
                               'title': 'nathandumont.com : Home', 
                               'num_pages': pages,
                               'pages': range(1, pages+1),
                               'page': limit + 1,
                               'next': next_page,
                               'prev': prev_page,
                               'page0': '/'})
  
  return HttpResponse(t.render(c))
  
def section(request, section, offset="1"):
  limit = int(offset) - 1
  sec = get_object_or_404(Section, url=section)
  posts = Post.objects.filter(published=True, special=False, section=sec).order_by('-last_modified')[limit*10:(limit+1)*10]
  
  num_posts = Post.objects.filter(published=True, special=False, section=sec).count()
  
  pages = int(ceil(num_posts / 10.0))
  
  if(limit > 0):
      prev_page = limit
  else:
      prev_page = False
  if(limit < pages-1):
      next_page = limit + 2
  else:
      next_page = False
  
  t = loader.get_template('blog/index.html')
  c = RequestContext(request, {'posts': posts, 'area': sec.title, 
                               'title': 'nathandumont.com : ' + sec.title, 
                               'num_pages': pages,
                               'pages': range(1, pages+1),
                               'page': limit + 1,
                               'next': next_page,
                               'prev': prev_page,
                               'page0': '/section/' + section + '/'})
  
  return HttpResponse(t.render(c))

def blog_page(request, slug):
  doc = get_object_or_404(Post, slug=slug, published=True, special=False)
  
  att = Attachment.objects.filter(post=doc).all()
  
  comments = Comment.objects.filter(post=doc, approved=True).all()
  
  tags = PostTag.objects.filter(post=doc)
  
  t = loader.get_template('blog/page.html')
  c = RequestContext(request, {'doc': doc, 'atts': att, 'comments': comments, 'tags': tags})
  
  return HttpResponse(t.render(c))

def special_page(request, slug):
    doc = get_object_or_404(Post, slug=slug, published=True, special=True)
    
    att = Attachment.objects.filter(post=doc)
    
    comments = Comment.objects.filter(post=doc, approved=True)
    
    tags = PostTag.objects.filter(post=doc)
    
    t = loader.get_template('blog/page.html')
    c = RequestContext(request, {'doc': doc, 'atts': att, 'comments': comments, 'tags': tags})
    
    return HttpResponse(t.render(c))

def legacy_node(request, nid):
  try:
    node = LegacyNode.objects.get(node=nid)
  except LegacyNode.DoesNotExist:
    node = get_object_or_404(ForeignNode, node=nid)
    return HttpResponsePermanentRedirect("http://hairymnstr.com/node/%d" % (node.node))
  return HttpResponsePermanentRedirect("/blog/" + node.post.slug)
  