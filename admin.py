import ew.models
from django.contrib import admin

class WordPairInline(admin.TabularInline):
    model = ew.models.WordPair
    extra = 1

class WordListAdmin(admin.ModelAdmin):
    inlines = [WordPairInline]

admin.site.register(ew.models.WDict, WordListAdmin)
