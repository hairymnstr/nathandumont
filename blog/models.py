from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings
import datetime, markdown, re
from django.template import loader, Context

from PIL import Image
from cStringIO import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
import os, cgi
# Create your models here.

def attributes_to_dict(attributes):
    d = {}
    for pair in attributes.split(","):
        kv = pair.split(":")
        if len(kv) == 1:
            d[kv[0].strip()] = True
        else:
            key = kv[0].strip()
            val = kv[1].strip()
            
            if(val.lower() == "true"):
                d[key] = True
            elif(val.lower() == "false"):
                d[key] = False
            elif(val.lower() == "none"):
                d[key] = None
            else:
                d[key] = val
    return d

class FilterProcessor:
    summary_start = 0
    summary_end = 1000
    incode = False
    code_language = None
    code_start = 0
    code_linenumbers = False
    refs_start = 0
    
    def __init__(self):
        self.figure_template = loader.get_template('blog/figure.html')
        self.gallery_template = loader.get_template('blog/gallery.html')
        self.group_template = loader.get_template('blog/group.html')
        self.tags = {
            'figure': self.tag_figure, 
            'summary': self.tag_summary,
            'code': self.tag_code,
            'gallery': self.tag_gallery,
            'refs': self.tag_refs,
            'group': self.post_group,
            }
        
    def run(self, md, slug):
        self.source = md
        self.slug = slug
        filter_re = re.compile(r'(?<!\\)\{(?P<tag_name>[a-zA-Z0-9\-_]+)\|(?P<attributes>.*?)\}')
        
        tokens = []
        pos = 0
        for m in filter_re.finditer(self.source):
            tokens.append(("literal", self.source[pos:m.start()]))
            tokens.append(("tag", m.group('tag_name'), m.group('attributes'), m.group(0)))
            pos = m.end()
            
        if(pos < len(self.source)):
            tokens.append(("literal", self.source[pos:]))
            
        self.output = ""
        for token in tokens:
            if(token[0] == "literal"):
                self.output += token[1]
            else:
                if self.incode and token[1] != "code":
                    self.output += token[3]
                else:
                    kw = attributes_to_dict(token[2])
                    self.tags[token[1]](**kw)
                
    
    def tag_figure(self, name=None, ref=None, thumbnail=True, title=True, caption=True, border=True):
        if name:
            """ This is a request to insert a named figure """
            fig = Figure.objects.get(label=name)
            self.output += self.figure_template.render(Context({"figure": fig,
                                                                "thumbnail": thumbnail,
                                                                "title": title,
                                                                "caption": caption,
                                                                "border": border}))
        else:
            """ This is a request to link to a named figure within this page """
            pass
    
    def tag_gallery(self, name):
        gallery = Gallery.objects.get(label=name)
        figures = Figure.objects.filter(gallery=gallery)
        
        self.output += self.gallery_template.render(Context({"figures": figures}))
        
    def tag_summary(self, start=False, end=False):
        if start:
            self.summary_start = len(self.output)
        if end:
            self.summary_end = len(self.output)

    def tag_code(self, begin=False, language=None, linenumbers=False, end=False):
        if end:
            """ Found the end of the code tag, process the output since code start """
            code_content = self.output[self.code_start:]
            
            # do syntax highlighting, linenumbers etc here
            
            self.output = (self.output[:self.code_start] + "<div class='code'><pre><code>"
                + code_content + "</code></pre></div>")
            self.incode = False
        else:
            """ Code start, store a global flag to treat the content as literal """
            self.incode = True
            self.code_language = language
            self.code_linenumbers = linenumbers
            self.code_start = len(self.output)
            
    def tag_refs(self, begin):
        self.refs_start = len(self.output)
        
    def get_rendered(self):
        return markdown.markdown(self.output, output_format="html5")
        
    def get_summary(self):
        if self.refs_start > 0:
            summary = self.output[self.summary_start:self.summary_end] + self.output[self.refs_start:]
        else:
            summary = self.output[self.summary_start:self.summary_end]
        return markdown.markdown(summary, output_format="html5")
        
    def post_group(self, name, two_column=False):
        postgroup = PostGroup.objects.get(slug=name)
        posts = PostGroupItem.objects.filter(group=postgroup)
        externals = ExternalGroupItem.objects.filter(group=postgroup)
        
        self.output += self.group_template.render(Context({"slug": self.slug,
                                                           "group": postgroup,
                                                           "posts": posts,
                                                           "externals": externals,
                                                           "two_column": two_column}))
        
class Post(models.Model):
  title = models.CharField(max_length=1000)
  slug = models.SlugField(blank=True, unique=True)
  last_modified = models.DateTimeField(blank=True)
  source = models.TextField()
  rendered = models.TextField(blank=True)
  summary = models.TextField(blank=True)
  published = models.BooleanField(default=False)
  special = models.BooleanField(default=False)
  reviewed = models.BooleanField(default=False)
  section = models.ForeignKey('Section')
  
  def __unicode__(self):
    return self.title
  
  def get_tags(self):
      return Tag.objects.filter(pk__in=PostTag.objects.filter(post=self).values_list('tag', flat=True))
      
  def get_attachments(self):
      return Attachment.objects.filter(post=self)
      
  def get_comments(self):
      return Comment.objects.filter(post=self, parent__isnull=True, approved=True).order_by('posted')
      
  def save(self, *args, **kwargs):
    if not self.id:
      self.slug = slugify(self.title[:Post._meta.get_field('slug').max_length])
      
    if not self.last_modified:
      self.last_modified = datetime.datetime.now()
      
    pr = FilterProcessor()
    pr.run(self.source, self.slug)
  
    self.rendered = pr.get_rendered()
    self.summary = pr.get_summary()
    super(Post, self).save(*args, **kwargs)

class Figure(models.Model):
  img = models.ImageField(upload_to="images")
  thumbnail = models.ImageField(upload_to="images", blank=True, null=True)
  title = models.CharField(max_length=50)
  caption = models.TextField(blank=True, null=True)
  label = models.SlugField(unique=True)
  gallery = models.ForeignKey('Gallery', blank=True, null=True)

  def __unicode__(self):
    return self.label
    
  def preview_tag(self):
      return u'<img src="%s" alt="%s"/>' % (self.thumbnail.url, self.caption)
  preview_tag.short_description = "Preview"
  preview_tag.allow_tags = True
      
  def make_thumbnail(self):
    if not self.img:
      return
    
    if (not isinstance(self.img.file, UploadedFile)) and (self.thumbnail):
      return
      
    THUMBNAIL_SIZE = (150, 150)
    
    if isinstance(self.img.file, UploadedFile):
      if self.img.file.content_type == 'image/jpeg':
        pil_type = 'jpeg'
        file_extension = 'jpg'
        content_type = 'image/jpeg'
      elif self.img.file.content_type == 'image/png':
        pil_type = 'png'
        file_extension = 'png'
        content_type = 'image/png'
    else:
      if os.path.splitext(self.img.name)[1].strip(".").lower() == "jpg":
        pil_type = 'jpeg'
        file_extension = 'jpg'
        content_type = 'image/jpeg'
      else:
        pil_type = 'png'
        file_extension = 'png'
        content_type = 'image/png'
        
    image = Image.open(StringIO(self.img.read()))
        
    image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
    
    temp = StringIO()
    image.save(temp, pil_type)
    temp.seek(0)
    
    fd = SimpleUploadedFile(os.path.split(self.img.name)[-1], 
                            temp.read(), content_type=content_type)
    
    thumbnail_name = "images/%s.preview.%s" % (os.path.splitext(fd.name)[0], file_extension)

    if(os.path.exists(os.path.join(settings.MEDIA_ROOT, thumbnail_name))):
      os.remove(os.path.join(settings.MEDIA_ROOT, thumbnail_name))
    self.thumbnail.save(thumbnail_name, fd, save=False)
    
  def scale_image(self):
    if not isinstance(self.img.file, UploadedFile):
      return
    
    if self.img.file.content_type == 'image/jpeg':
      pil_type = 'jpeg'
      file_extension = '.jpg'
    elif self.img.file.content_type == 'image/png':
      pil_type = 'png'
      file_extension = '.png'
    
    if hasattr(self.img.file, 'temporary_file_path'):
      image = Image.open(self.img.file.temporary_file_path())
    else:
      # thumbnail will have already read the file from memory
      self.img.file.seek(0)
      image = Image.open(StringIO(self.img.file.read()))
    
    image.thumbnail((1600, 1600), Image.ANTIALIAS)
    
    temp = StringIO()
    image.save(temp, pil_type)
    temp.seek(0)
    
    fd = SimpleUploadedFile(os.path.splitext(self.img.name)[0] + file_extension, 
                            temp.read(),
                            content_type=self.img.file.content_type)
    
    self.img.save(os.path.splitext(self.img.name)[0] + file_extension, fd, save=False)
    
  def save(self, *args, **kwargs):
    self.make_thumbnail()
    self.scale_image()
    super(Figure, self).save(*args, **kwargs)

class Gallery(models.Model):
  title = models.CharField(max_length=100)
  label = models.SlugField(unique=True, blank=True)
  hidden = models.BooleanField(default=True)
  description = models.TextField(blank=True, default="")
  gallery_date = models.DateTimeField(default=datetime.datetime.now, blank=True)
  
  def __unicode__(self):
    return self.title + " (" + self.label + ")"
    
  def save(self, *args, **kwargs):
    if not self.id:
      self.label = slugify(self.title)
      
    super(Gallery, self).save(*args, **kwargs)
    
  def cover_image(self):
    return Figure.objects.filter(gallery=self.id)[0]

class Attachment(models.Model):
  file = models.FileField(upload_to="uploads")
  updated = models.DateTimeField(auto_now=True)
  description = models.CharField(max_length=256)
  post = models.ForeignKey('Post')
  size = models.IntegerField(blank=True)
  
  def __unicode__(self):
    return unicode(self.file)
    
  def save(self, *args, **kwargs):
    if isinstance(self.file.file, UploadedFile):
      self.size = self.file.size
      
    super(Attachment, self).save(*args, **kwargs)

class Comment(models.Model):
  title = models.CharField(max_length=100)
  content = models.TextField()
  posted = models.DateTimeField(blank=True)
  posted_by = models.CharField(max_length=100)
  post = models.ForeignKey('Post')
  parent = models.ForeignKey('Comment', blank=True, null=True)
  approved = models.BooleanField(default=False)
  
  def __unicode__(self):
      return self.posted_by +": \"" + self.title + "\""
      
  def get_children(self):
      return Comment.objects.filter(parent=self, approved=True).order_by('posted')
      
  def content_cleaned(self):
      are = re.compile('<a .*?href=[\'"]([^\'"]+)[\'"].*?>([^<>]+)</a>')
      
      pos = 0
      m = are.search(self.content, pos)
      output = ""
      while m:
          output += cgi.escape(self.content[pos:m.start()])
          output += "<a href=\""
          output += m.group(1).replace("&amp;", "&").replace("&", "&amp;")
          output += "\">"
          output += cgi.escape(m.group(2))
          output += "</a>"
          pos = m.end()
          m = are.search(self.content, pos)
      output += cgi.escape(self.content[pos:])
      
      return "<p>" + "<br/>".join(output.splitlines()) + "</p>"
      
  def save(self, *args, **kwargs):
    if not self.posted:
      self.posted = datetime.datetime.now()
    super(Comment, self).save(*args, **kwargs)
  
class Section(models.Model):
  title = models.CharField(max_length=100)
  url = models.SlugField(blank=True, unique=True)
  
  def __unicode__(self):
    return self.title
    
  def save(self, *args, **kwargs):
    if not self.id:
      self.url = slugify(self.title)
      
    super(Section, self).save(*args, **kwargs)
    
class LegacyNode(models.Model):
  node = models.IntegerField()
  post = models.ForeignKey('Post')
  
  def __unicode__(self):
      return self.post.title + " [" + unicode(self.node) + "]"
  
class ForeignNode(models.Model):
  node = models.IntegerField()
  
  def __unicode__(self):
      return "hairymnstr.com/node/" + unicode(self.node)
  
class Tag(models.Model):
  text = models.CharField(max_length=100)
  slug = models.SlugField(blank=True, unique=True)
  legacyId = models.IntegerField(blank=True, null=True)
  
  def __unicode__(self):
    return self.text
    
  def save(self, *args, **kwargs):
    if not self.id:
      self.slug = slugify(self.text[:Tag._meta.get_field('slug').max_length])
    
    super(Tag, self).save(*args, **kwargs)

class PostTag(models.Model):
  tag = models.ForeignKey('Tag')
  post = models.ForeignKey('Post')
  
  def __unicode__(self):
    return self.post.title + " [" + self.tag.text + "]"

class PostGroup(models.Model):
    group_name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, unique=True)
    
    def __unicode__(self):
        return self.group_name
          
    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.group_name[:PostGroup._meta.get_field('slug').max_length])
        
        super(PostGroup, self).save(*args, **kwargs)
        
class PostGroupItem(models.Model):
    group = models.ForeignKey('PostGroup')
    post = models.ForeignKey('Post')
    weight = models.IntegerField(default=0)
    is_summary = models.BooleanField(default=False)
    
    def __unicode__(self):
        return "[" + self.group.group_name + "] " + self.post.title
        
class ExternalGroupItem(models.Model):
    group = models.ForeignKey('PostGroup')
    url = models.URLField()
    description = models.CharField(max_length=100, blank=True)
    weight = models.IntegerField(default=0)
    
    def __unicode__(self):
        if self.description == "":
            return "[" + self.group.group_name + "] " + self.url
        else:
            return "[" + self.group.group_name + "] " + self.description
