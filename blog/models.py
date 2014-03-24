from django.db import models
import markdown
import re
from django.template.defaultfilters import slugify
from django.template import loader, Context

# Create your models here.

def do_markdown(source):
  subjects = Post.objects.all()
  
  t = loader.get_template("figure.html")
  
  # generate automatic image thumbnails
  r = re.compile("(\{[a-zA-Z0-9_\-]*\})")
  
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
      slug = token[0].strip("{}")
    
      try:
        fig = Figure.objects.get(label=slug)
      except Figure.DoesNotExist:
        fig = None
      
      if fig != None:
        output += t.render(Context({"figure": fig}))
  
  # generate references for automatic links
  refs = ""
  for s in subjects:
    refs += "[" + s.title + "]: /blog/" + s.slug + "\"" + s.title + "\"\n"
  return markdown.markdown(output + "\n\n" + refs, output_format="html5")

class Post(models.Model):
  title = models.CharField(max_length=1000)
  slug = models.SlugField(blank=True, unique=True)
  last_modified = models.DateTimeField(auto_now=True)
  source = models.TextField()
  rendered = models.TextField(blank=True)
  published = models.BooleanField(default=False)
  
  def __unicode__(self):
    return self.title
    
  def save(self, *args, **kwargs):
    if not self.id:
      self.slug = slugify(self.title)
      
    self.rendered = do_markdown(self.source)
    super(Post, self).save(*args, **kwargs)

class Figure(models.Model):
  img = models.ImageField(upload_to="images")
  thumbnail = models.ImageField(upload_to="images", blank=True, null=True)
  title = models.CharField(max_length=50)
  caption = models.TextField()
  label = models.SlugField(unique=True)
  
  def __unicode__(self):
    return self.label
    
  def make_thumbnail(self):
    if not self.img:
      return
      
    from PIL import Image
    from cStringIO import StringIO
    from django.core.files.uploadedfile import SimpleUploadedFile
    import os
    
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
    
    fd = SimpleUploadedFile(os.path.split(self.img.name)[-1], temp.read(), content_type=self.img.file.content_type)
    
    self.thumbnail.save("%s.preview.%s" % (os.path.splitext(fd.name)[0], file_extension), fd, save=False)
    
  def save(self):
    self.make_thumbnail()
    super(Figure, self).save()

class Attachment(models.Model):
  file = models.FileField(upload_to="uploads")
  updated = models.DateTimeField(auto_now=True)
  description = models.CharField(max_length=256)
  post = models.ForeignKey('Post')
  
class Comment(models.Model):
  title = models.CharField(max_length=100)
  content = models.TextField()
  posted = models.DateTimeField(auto_now_add=True)
  posted_by = models.CharField(max_length=100)
  post = models.ForeignKey('Post')
  parent = models.ForeignKey('Comment', blank=True)
  approved = models.BooleanField(default=False)
  
class LegacyNode(models.Model):
  node = models.IntegerField()
  post = models.ForeignKey('Post')
  