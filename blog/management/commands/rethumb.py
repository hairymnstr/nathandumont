from django.core.management.base import BaseCommand, CommandError
from blog.models import Figure
import sys, os

class Command(BaseCommand):
    args = ''
    help = """Loads each figure and regenerates the thumbnail image for it."""
    
    def handle(self, *args, **kwargs):
        for figure in Figure.objects.all():
            self.stdout.write("Updating " + figure.title + "...")
            self.stdout.flush()
            figure.thumbnail=""
            figure.save()
            self.stdout.write("Done\n")
