from django.db import models
import datetime


class WordList(models.Model):

    name = models.CharField(max_length=255) # the name of the wordlist

    def __unicode__(self):
        return self.name


class Word(models.Model):

    # each word belongs to a wordlist
    wordlist = models.ForeignKey(WordList)

    # the form of the word in the first/second language:
    lang0 = models.CharField(max_length=255)
    lang1 = models.CharField(max_length=255)

    # strengths of the word
    strength0 = models.IntegerField(default=0)
    strength1 = models.IntegerField(default=0)

    # dates of the next practice
    date0 = models.DateField(default=datetime.date.today())
    date1 = models.DateField(default=datetime.date.today())

    # explanation, examples, comments, etc.
    explanation = models.TextField(blank=True)

    def __unicode__(self):
        return ('<%s -- %s>' %
                (repr(self.lang0), repr(self.lang1)))

