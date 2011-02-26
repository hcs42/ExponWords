import datetime
from django.db import models
from django.contrib.auth.models import User


class WDict(models.Model):

    # WDict = word dictionary (as opposed to the dictionary data type which is
    # an "object dictionary")

    user = models.ForeignKey(User)
    name = models.CharField(max_length=255) # the name of the dictionary
    lang1 = models.CharField(max_length=255)
    lang2 = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class WordPair(models.Model):

    # each word pair belongs to a dictionary
    wdict = models.ForeignKey(WDict)

    # the word in the first/second language:
    word_in_lang1 = models.CharField(max_length=255)
    word_in_lang2 = models.CharField(max_length=255)

    # strengths of the word
    strength1 = models.IntegerField(default=0)
    strength2 = models.IntegerField(default=0)

    # dates of the next practice
    date_added = models.DateField(default=datetime.date.today())
    date1 = models.DateField(default=datetime.date.today())
    date2 = models.DateField(default=datetime.date.today())

    # explanation, examples, comments, etc.
    explanation = models.TextField(blank=True)

    def __unicode__(self):
        return ('<%s -- %s>' %
                (repr(self.word_in_lang1), repr(self.word_in_lang2)))

