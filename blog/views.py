from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template import RequestContext, loader
from django.shortcuts import get_object_or_404
from blog.models import Post, LegacyNode, ForeignNode, Attachment, Comment, Section, PostTag, Tag
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

def tagged_posts(request, tag_name, offset="1"):
  limit = int(offset) - 1
  tag = get_object_or_404(Tag, slug=tag_name)
  post_tags = PostTag.objects.filter(tag=tag).values_list('post', flat=True)
  posts = Post.objects.filter(published=True, special=False, pk__in=post_tags).order_by('-last_modified')[limit*10:(limit+1)*10]
  
  num_posts = Post.objects.filter(published=True, special=False, pk__in=post_tags).count()
  
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
  c = RequestContext(request, {'posts': posts, 'area': tag.text, 
                               'title': 'nathandumont.com : ' + tag.text, 
                               'num_pages': pages,
                               'pages': range(1, pages+1),
                               'page': limit + 1,
                               'next': next_page,
                               'prev': prev_page,
                               'page0': '/tag/' + tag_name + '/'})
  
  return HttpResponse(t.render(c))

def tree_comments(comment, depth):
    comm_list = []
    comm_list.append((comment, depth))
    for comm in comment.get_children():
        comm_list.extend(tree_comments(comm, depth+1))
    return comm_list
        
def blog_page(request, slug):
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
  c = RequestContext(request, {'post': post, 'atts': att, 'comments': dl})
  
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
  