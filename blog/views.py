from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template import RequestContext, loader
from django.shortcuts import get_object_or_404
from blog.models import Post, LegacyNode
# Create your views here.

def blog_home(request):
  
  t = loader.get_template('blog/home.html')
  c = RequestContext(request, {})
  
  return HttpResponse(t.render(c))
  
def blog_page(request, slug):
  doc = get_object_or_404(Post, slug=slug)
  
  t = loader.get_template('blog/page.html')
  c = RequestContext(request, {'doc': doc})
  
  return HttpResponse(t.render(c))

#def docs_index(request):
  #doc = Subject.objects.all()
  
  #t = loader.get_template('docs/index.html')
  #c = RequestContext(request, {'docs': doc, 'area': 'Hardware Documentation'})
  
  #return HttpResponse(t.render(c))

def legacy_node(request, nid):
  node = get_object_or_404(LegacyNode, node=nid)
  
  return HttpResponsePermanentRedirect("/blog/" + node.post.slug)