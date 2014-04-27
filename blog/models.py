from django.db import models
import markdown
import re
from django.template.defaultfilters import slugify
from django.template import loader, Context
import datetime
from filterprocessor import FilterProcessor

from PIL import Image
from cStringIO import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
import os
# Create your models here.

def do_markdown(source):
  summary_start = 0
  summary_end = 1000
  t = loader.get_template("figure.html")
  figurent_template = loader.get_template("figurent.html")
  gallery_template = loader.get_template("gallery.html")
  
  # generate automatic image thumbnails
  r = re.compile("(\{[a-zA-Z0-9_\-]*\|[a-zA-Z0-9_\-:]*\})")
  
  tokens = []
  pos = 0
  output = ""
  for m in r.finditer(source):
    tokens.append((source[pos:m.start()], "literal"))
    tokens.append((source[m.start():m.end()], "keyword"))
    pos = m.end()
    
  if pos < len(source):
    tokens.append((source[pos:], "literal"))
  
  for token in tokens:
    if(token[1] == "literal"):
      output += token[0]
    else:
      command, parameter = token[0].strip("{}").split("|")
      
      if command == "figure":
        slug = parameter
      
        try:
          fig = Figure.objects.get(label=slug)
        except Figure.DoesNotExist:
          fig = None
        
        if fig != None:
          output += t.render(Context({"figure": fig}))
      elif command == "figurent":
        # figure with no thumbnail, show the img itself with no link
        try:
          fig = Figure.objects.get(label=parameter)
        except Figure.DoesNotExist:
          fig = None
          
        if fig != None:
          output += figurent_template.render(Context({"figure": fig}))
      elif command == "summary":
        if parameter == "start":
          summary_start = len(output)
        elif parameter == "end":
          summary_end = len(output)
      elif command == "gallery":
        slug = parameter
        
        try:
          gallery = Gallery.objects.get(label=slug)
        except Gallery.DoesNotExist:
          gallery = None
          
        if gallery != None:
          figs = Figure.objects.filter(gallery = gallery)
          output += gallery_template.render(Context({"gallery": gallery, "figures": figs}))
  
  return markdown.markdown(output, output_format="html5"), markdown.markdown(output[summary_start:summary_end], output_format="html5")

class Post(models.Model):
  title = models.CharField(max_length=1000)
  slug = models.SlugField(blank=True, unique=True)
  last_modified = models.DateTimeField(blank=True)
  source = models.TextField()
  rendered = models.TextField(blank=True)
  summary = models.TextField(blank=True)
  published = models.BooleanField(default=False)
  section = models.ForeignKey('Section')
  
  def __unicode__(self):
    return self.title
    
  def save(self, *args, **kwargs):
    if not self.id:
      self.slug = slugify(self.title[:Post._meta.get_field('slug').max_length])
      
    if not self.last_modified:
      self.last_modified = datetime.datetime.now()
      
    self.rendered, self.summary = do_markdown(self.source)
    super(Post, self).save(*args, **kwargs)

class Figure(models.Model):
  img = models.ImageField(upload_to="images")
  thumbnail = models.ImageField(upload_to="images", blank=True, null=True)
  title = models.CharField(max_length=50)
  caption = models.TextField()
  label = models.SlugField(unique=True)
  gallery = models.ForeignKey('Gallery', blank=True, null=True)
  
  def __unicode__(self):
    return self.label
    
  def make_thumbnail(self):
    if not self.img:
      return
    
    if not isinstance(self.img.file, UploadedFile):
      return
      
    THUMBNAIL_SIZE = (150, 150)
    
    if self.img.file.content_type == 'image/jpeg':
      pil_type = 'jpeg'
      file_extension = 'jpg'
    elif self.img.file.content_type == 'image/png':
      pil_type = 'png'
      file_extension = 'png'
    
    image = Image.open(StringIO(self.img.read()))
    
    image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
    
    temp = StringIO()
    image.save(temp, pil_type)
    temp.seek(0)
    
    fd = SimpleUploadedFile(os.path.split(self.img.name)[-1], 
                            temp.read(), content_type=self.img.file.content_type)
    
    self.thumbnail.save("%s.preview.%s" % (os.path.splitext(fd.name)[0], file_extension), 
                        fd, save=False)
    
  def save(self, *args, **kwargs):
    self.make_thumbnail()
    super(Figure, self).save(*args, **kwargs)

class Gallery(models.Model):
  title = models.CharField(max_length=100)
  label = models.SlugField(unique=True, blank=True)
  
  def __unicode__(self):
    return self.title + " (" + self.label + ")"
    
  def save(self, *args, **kwargs):
    if not self.id:
      self.label = slugify(self.title)
      
    super(Gallery, self).save(*args, **kwargs)

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
