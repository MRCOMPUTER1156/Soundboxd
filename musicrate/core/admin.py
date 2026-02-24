from django.contrib import admin
from .models import Artist, Album, Review

admin.site.register(Artist)
admin.site.register(Album)
admin.site.register(Review)