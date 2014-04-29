from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from blog.models import Post
import re

def make_absolute(summary):
    re_img = re.compile('((?:<img[^<>]*?src=["\'])|(?:<a[^<>]*?href=[\'"]))([^\'"]+)([\'"][^<>]*>)')
    tokens = []
    pos = 0
    for m in re_img.finditer(summary):
        tokens.append(("literal", summary[pos:m.start()]))
        tokens.append(("tag", m.group(0), m.group(1), m.group(2), m.group(3)))
        pos = m.end()
    if(pos < len(summary)):
        tokens.append(("literal", summary[pos:]))
    output = ""
    for token in tokens:
        if token[0] == "literal":
            output += token[1]
        else:
            if token[3][0] == "/":
                output += token[2] + "http://nathandumont.com" + token[3] + token[4]
            else:
                output += token[1]
    return output
                
class LatestEntriesFeed(Feed):
    title = "Posts from nathandumont.com"
    link = "/"
    description = "Latest articles from all categories on nathandumont.com"

    def items(self):
        return Post.objects.filter(published=True, special=False).order_by('-last_modified')[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return make_absolute(item.summary)

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return reverse('post-view', args=[item.slug])
