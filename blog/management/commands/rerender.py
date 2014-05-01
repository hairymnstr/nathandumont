from django.core.management.base import BaseCommand, CommandError
from blog.models import Post
import sys, os

class Command(BaseCommand):
    args = ''
    help = """Loads each post and re-generates the rendered view.  Useful after updates to 
gallery/figure templates."""
    
    def handle(self, *args, **kwargs):
        for post in Post.objects.all():
            self.stdout.write("Updating " + post.title + "...")
            self.stdout.flush()
            post.save()
            self.stdout.write("Done\n")