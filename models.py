# This file is part of ExponWords.
#
# ExponWords is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# ExponWords is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# ExponWords.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2011 Csaba Hoch

import datetime
import random
import re
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


version = '0.3.2'


class WDict(models.Model):

    # WDict = word dictionary (as opposed to the dictionary data type which is
    # an "object dictionary")

    user = models.ForeignKey(User)
    name = models.CharField(max_length=255) # the name of the dictionary
    lang1 = models.CharField(max_length=255)
    lang2 = models.CharField(max_length=255)
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_words_to_practice_today(self):
        today = datetime.date.today()
        result = []
        for wp in self.wordpair_set.filter(deleted=False):
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
    date_added = models.DateField()
    date1 = models.DateField()
    date2 = models.DateField()

    # explanation, examples, comments, etc.
    explanation = models.TextField(blank=True)

    # whether the word pair is deleted or not
    deleted = models.BooleanField(default=False)

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
        new_strength = min(self.get_strength(direction), 0)
        self.set_strength(direction, new_strength)


class EWException(Exception):
    """A very simple exception class used."""

    def __init__(self, value):
        """Constructor.

        **Argument:**

        - `value` (object) -- The reason of the error.
        """
        Exception.__init__(self)
        self.value = value

    def __unicode__(self):
        """Returns the string representation of the error reason.

        **Returns:** str
        """

        value = self.value
        if isinstance(value, unicode):
            return value
        elif isinstance(value, str):
            return unicode(value)
        else:
            return repr(value)


def create_add_word_pairs(wdict, word_pairs):
    for wp in word_pairs:
        wdict.wordpair_set.add(wp)
        wp.save()
        wdict.save()


def import_textfile(s, wdict):
    """Adds words from a text file to a dictionary.

    Arguments:
    - s (str)
    - wdict (WDict)
    """

    i = 1
    word_pairs = []
    for line in s.splitlines():
        line = line.rstrip()
        if (line == '') or (line[0] == ' '):
            # This line is part of an explanation.
            if len(word_pairs) != 0:
                line = re.sub('^ {1,4}', '', line) # removing prefix spaces
                word_pairs[-1].explanation += line + '\n'
            elif line == '':
                pass
            else:
                msg = (_('Line %(linenumber)s should not have spaces in '
                         'the beginning: %(line)s') %
                       {'linenumber': i, 'line': line})
                raise EWException(msg)
        else:
            # This line contains a word pair.
            strength_date_regexp = '<(-?\d+) +(\d\d\d\d)-(\d\d)-(\d\d)>'
            regexp = (r'^(\{(\d+)\})? *(.*?) -- (.*?)' +
                      '( ' + strength_date_regexp * 2 + ')?' +
                      '$')
            r = re.search(regexp, line)
            if r is None:
                msg = (_('Line %(linenumber)s is incorrect: %(line)s') %
                       {'linenumber': i, 'line': line})
                raise EWException(msg)

            wp = WordPair()
            word_pairs.append(wp)

            wp.word_in_lang1 = r.group(3)
            wp.word_in_lang2 = r.group(4)
            wp.explanation = ''
            if r.group(5) is not None:
                wp.date_added = datetime.date.today()
                wp.date1 = datetime.date(int(r.group(7)),
                                         int(r.group(8)),
                                         int(r.group(9)))
                wp.date2 = datetime.date(int(r.group(11)),
                                         int(r.group(12)),
                                         int(r.group(13)))
                wp.strength1 = int(r.group(6))
                wp.strength2 = int(r.group(10))
            else:
                wp.date_added = datetime.date.today()
                wp.date1 = datetime.date.today()
                wp.date2 = datetime.date.today()
                wp.strength1 = 0
                wp.strength2 = 0

        i += 1

    create_add_word_pairs(wdict, word_pairs)

def import_tsv(s, wdict):
    """Adds words from a text of tab-separeted values to a dictionary.

    Arguments:
    - s (str)
    - wdict (WDict)
    """

    i = 1
    word_pairs = []
    for line in s.splitlines():
        line = line.strip()
        if (line == ''):
            continue

        fields = line.split('\t')
        if len(fields) < 2:
            msg = (_('Not enough fields in line %(linenumber)s: %(line)s') %
                   {'linenumber': i, 'line': line})
            raise EWException(msg)
        elif 2 <= len(fields) <= 3:
            wp = WordPair()
            wp.word_in_lang1 = fields[0]
            wp.word_in_lang2 = fields[1]
            if len(fields) == 3:
                wp.explanation = fields[2]
            wp.date1 = datetime.date.today()
            wp.date2 = datetime.date.today()
            wp.date_added = datetime.date.today()
            word_pairs.append(wp)
        else:
            msg = (_('Too many fields in line %(linenumber)s: %(line)s') %
                   {'linenumber': i, 'line': line})
            raise EWException(msg)

        i += 1
    
    create_add_word_pairs(wdict, word_pairs)


def export_textfile(wdict):
    """Prints a dictionary in the old text format.

    Arguments:
    - wdict (WDict)

    Returns: str
    """

    result = []
    for wp in wdict.wordpair_set.filter(deleted=False):
        result.append(
            '%s -- %s <%s %s><%s %s>\n' %
            (wp.word_in_lang1,
             wp.word_in_lang2,
             str(wp.strength1),
             str(wp.date1),
             str(wp.strength2),
             str(wp.date2)))
        for expl_line in wp.explanation.splitlines():
            if expl_line != '':
                result.append('    ')
                result.append(expl_line)
            result.append('\n')
    return ''.join(result)


class EWLogEntry(models.Model):
    
    datetime = models.DateTimeField()
    action = models.TextField()
    user = models.ForeignKey(User, blank=True, null=True)
    username = models.TextField(blank=True)
    text = models.TextField(blank=True)
    ipaddress = models.TextField(blank=True)


def log(request, action, text=''):

    logentry = EWLogEntry()
    logentry.datetime = datetime.datetime.now()
    try:
        logentry.action = action
        logentry.ipaddress = (request.META.get('REMOTE_ADDR' , '') + ', ' +
                              request.META.get('HTTP_X_FORWARDED_FOR', ''))
        if request.user.is_authenticated():
            logentry.user = request.user
            logentry.username = request.user.username

        logentry.text = text
    except Exception, e:
        logentry.action = 'Logging failed'
    logentry.save()
