import datetime
import random
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

    def get_words_to_practice_today(self):
        today = datetime.date.today()
        result = []
        for wp in self.wordpair_set.all():
            if wp.date1 <= today:
                result.append((wp, 1))
            if wp.date2 <= today:
                result.append((wp, 2))
        random.shuffle(result)
        return result




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

    def get_strength(self, direction):
        if direction == 1:
            return self.strength1
        else:
            return self.strength2

    def set_strength(self, direction, value):
        if direction == 1:
            self.strength1 = value
        else:
            self.strength2 = value

    def get_date(self, direction):
        if direction == 1:
            return self.date1
        else:
            return self.date2

    def set_date(self, direction, value):
        if direction == 1:
            self.date1 = value
        else:
            self.date2 = value

    def next_date(self, strength):
        if strength < 0:
            strength = 0
        return datetime.date.today() + datetime.timedelta(2 ** strength)

    def strengthen(self, direction):
        strength = self.get_strength(direction)
        self.set_date(direction, self.next_date(strength))
        self.set_strength(direction, self.get_strength(direction) + 1)

    def weaken(self, direction):
        self.set_date(direction, datetime.date.today())
        self.set_strength(direction, 0)
