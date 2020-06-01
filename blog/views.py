from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template import loader
from django.shortcuts import get_object_or_404
from blog.models import Post, LegacyNode, ForeignNode, Attachment, Comment, Section, PostTag, Tag, Gallery
from math import ceil
from django.contrib.sites.models import Site
# Create your views here.

def template_name():
  return "base_" + Site.objects.get_current().domain + ".html"

def pagination(num_posts, limit, url_base):
    pages = int(ceil(num_posts / 10.0))
  
    if(limit > 0):
        prev_page = limit
    else:
        prev_page = False
    if(limit < pages-1):
        next_page = limit + 2
    else:
        next_page = False

    t = loader.get_template('blog/paginator.html')
    c = {
        'num_pages': pages,
        'pages': range(1, pages+1),
        'page': limit + 1,
        'next': next_page,
        'prev': prev_page,
        'page0': url_base
    }
    return t.render(c)

def home(request, offset="1"):
  current_site = Site.objects.get_current()
  limit = int(offset) - 1
  posts = Post.objects.filter(published=True, special=False).order_by('-last_modified')[limit*10:(limit+1)*10]
  
  num_posts = Post.objects.filter(published=True, special=False).count()
  
  paginator = pagination(num_posts, limit, '/')
  
  t = loader.get_template('blog/index.html')
  c = {
    'base_template': template_name(),
    'posts': posts, 'area': 'Home', 
    'title': current_site.domain + ' : Home', 
    'paginator': paginator
  }
 
  return HttpResponse(t.render(c, request))
  
def section(request, section, offset="1"):
  current_site = Site.objects.get_current()
  limit = int(offset) - 1
  sec = get_object_or_404(Section, url=section)
  posts = Post.objects.filter(published=True, special=False, section=sec).order_by('-last_modified')[limit*10:(limit+1)*10]
  
  num_posts = Post.objects.filter(published=True, special=False, section=sec).count()
  paginator = pagination(num_posts, limit, '/section/' + section + '/') 
  
  t = loader.get_template('blog/index.html')
  c = {
    'base_template': template_name(),
    'posts': posts, 'area': sec.title, 
    'title': current_site.domain + ' : ' + sec.title,
    'paginator': paginator
  }
  
  return HttpResponse(t.render(c, request))

def tagged_posts(request, tag_name, offset="1"):
  current_site = Site.objects.get_current()
  limit = int(offset) - 1
  tag = get_object_or_404(Tag, slug=tag_name)
  post_tags = PostTag.objects.filter(tag=tag).values_list('post', flat=True)
  posts = Post.objects.filter(published=True, special=False, pk__in=post_tags).order_by('-last_modified')[limit*10:(limit+1)*10]
  
  num_posts = Post.objects.filter(published=True, special=False, pk__in=post_tags).count()
  paginator = pagination(num_posts, limit, '/tag/' + tag_name + '/')
  
  t = loader.get_template('blog/index.html')
  c = {
    'base_template': template_name(),
    'posts': posts,
    'area': tag.text, 
    'title': current_site.domain + ' : ' + tag.text,
    'paginator': paginator
  }
  
  return HttpResponse(t.render(c, request))

def tree_comments(comment, depth):
    comm_list = []
    comm_list.append((comment, depth))
    for comm in comment.get_children():
        comm_list.extend(tree_comments(comm, depth+1))
    return comm_list
        
def blog_page(request, slug):
  current_site = Site.objects.get_current()
  post = get_object_or_404(Post, slug=slug, published=True, special=False)
  
  att = Attachment.objects.filter(post=post).all()
  
  comments = post.get_comments()
  dl = None
  if(comments):
    recursed_comments = []
    for comment in comments:
        recursed_comments.extend(tree_comments(comment, 0))
    
    dl = []
    for i in range(len(recursed_comments)-1):
        depths_to_close = range(recursed_comments[i][1] - recursed_comments[i+1][1] + 1)
        dl.append((recursed_comments[i][0], depths_to_close))
    
    dl.append((recursed_comments[-1][0], range(recursed_comments[-1][1]+1)))
  
  t = loader.get_template('blog/page.html')
  c = {
    'base_template': template_name(),
    'site': current_site,
    'post': post, 
    'atts': att, 
    'comments': dl
  }
  
  return HttpResponse(t.render(c, request))

def special_page(request, slug):
    current_site = Site.objects.get_current()
    doc = get_object_or_404(Post, slug=slug, published=True, special=True)
    
    att = Attachment.objects.filter(post=doc)
    
    comments = Comment.objects.filter(post=doc, approved=True)
    
    tags = PostTag.objects.filter(post=doc)
    
    t = loader.get_template('blog/page.html')
    c = {
        'base_template': template_name(),
        'site': current_site,
        'post': doc, 
        'atts': att, 
        'comments': None
    }
    
    return HttpResponse(t.render(c, request))

def legacy_node(request, nid):
  try:
    node = LegacyNode.objects.get(node=nid)
  except LegacyNode.DoesNotExist:
    node = get_object_or_404(ForeignNode, node=nid)
    return HttpResponsePermanentRedirect("http://hairymnstr.com/node/%d" % (node.node))
  return HttpResponsePermanentRedirect("/blog/" + node.post.slug)
  
def gallery_index(request):
    current_site = Site.objects.get_current()
    galleries = Gallery.objects.filter(hidden=False).order_by('-gallery_date')
    
    t = loader.get_template('blog/gallery_index.html')
    c = {
        'base_template': template_name(),
        'site': current_site,
        'galleries': galleries
    }
    
    return HttpResponse(t.render(c, request))

def gallery(request, slug):
    current_site = Site.objects.get_current()
    gallery = get_object_or_404(Gallery, label=slug)
    
    t = loader.get_template('blog/gallery_live.html')
    c = {
        'base_template': template_name(),
        'site': current_site,
        'gallery': gallery
    }
    
    return HttpResponse(t.render(c, request))
