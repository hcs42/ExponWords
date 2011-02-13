import ew.models
from django.contrib import admin

class WordInline(admin.TabularInline):
    model = ew.models.Word
    extra = 1

class WordListAdmin(admin.ModelAdmin):
    inlines = [WordInline]

admin.site.register(ew.models.WordList, WordListAdmin)
