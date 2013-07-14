# Copyright (C) 2011-2013 Csaba Hoch
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import math
import random
import re
import sys
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


version = '0.13.6'

##### Constants #####

# The maximum number of characters used to represent a word
WORD_PREFIX = 40;

# The minimum dimness required for a word to be practiced during "early
# practice". The dimness of 0.75 means that:
#
#     actual_interval_len = 0.75 * due_interval
#     due_interval2_len = 2 * actual_interval_len = 1.5 * due_interval_len
#
#     strength1 = 1 + log_2 due_interval_len
#     strength2 = 1 + log_2 due_interval2_len
#
# From these:
#
#     strength2 = 1 + log_2 1.5 * due_interval_len
#     strength2 = 1 + log_2 1.5 + log_2 due_interval_len
#     strength2 = 1 + log_2 due_interval_len + log_2 1.5
#     strength2 = strength1 + log_2 1.5
#     strength2 = strength1 + 0.5850
#
# General equasion:
#
#     log_2 2 * (MIN_DIMNESS_FOR_EARLY_PRACTICE) = strength_increment; i.e.
#     MIN_DIMNESS_FOR_EARLY_PRACTICE = (2 ^ strength_increment) / 2
MIN_DIMNESS_FOR_EARLY_PRACTICE = 0.75;


##### Utility functions #####

def unexpected_value(name, value):
    msg = 'Unexpected value for variable "%s": %s' % (name, value)
    raise EWException(msg)


##### Date handling #####


# General concept:
#
# words at DAY shall be asked
# if user_time(utc) >= DAY_00:00
# where user_time = now_utc + timezone - turning_point

# Example (DAY example in backets):
#
# timezone: UTC+2 (CEST) -> 2:00
# turning_point: 3:00
# words at 2011-01-10 shall be asked
# if user_time + 2:00 - 3:00 >= 2011-01-10_00:00
# if user_time >= 2011-01-10_01:00


def get_user_time(user=None, timezone=None, turning_point=None, now=None):

    # set timezone and turning_point
    if user is not None:
        ewuser = get_ewuser(user)
        timezone = ewuser.timezone
        turning_point = ewuser.turning_point
    elif (timezone is None or turning_point is None):
        raise EWException('get_user_time: Either the user or the timezone '
                          'and the turning_point parameter has to be not None')

    # set `now`
    if now is None:
        now = datetime.datetime.utcnow()

    return (now
            + datetime.timedelta(hours=timezone)
            - datetime.timedelta(minutes=turning_point))


def is_word_due(word_date, user_time):
    word_dt_0 = datetime.datetime(year=word_date.year,
                                  month=word_date.month,
                                  day=word_date.day)
    return user_time >= word_dt_0


def get_today(user=None, timezone=None, turning_point=None, now=None):
    user_time = get_user_time(user, timezone, turning_point, now)
    return datetime.date(user_time.year, user_time.month, user_time.day)


##### Model classes #####


class EWUser(models.Model):

    user = models.OneToOneField(User, primary_key=True)

    # The language of the user interface
    lang = models.CharField(max_length=10, default='en')

    # Time difference with UTC in hours (positive value means east from GMT)
    timezone = models.IntegerField(default=0)

    # How many minutes after midnight should we ask the words of the new day
    # (may be negative)
    turning_point = models.IntegerField(default=0)

    # Word order on practice page
    practice_word_order = models.CharField(default='random', max_length=20)

    # Practice page arrangement
    practice_arrangement = models.CharField(default='normal', max_length=20)
    quick_labels = models.CharField(default='quick', max_length=255, blank=True)

    # Font sizes on the practice page
    button_size = models.IntegerField(default=35)
    question_size = models.IntegerField(default=20)
    answer_size = models.IntegerField(default=20)
    explanation_size = models.IntegerField(default=20)

    # Whether the user wants to receive emails about new ExponWords features
    release_emails = models.BooleanField(default=True)

    def __unicode__(self):
        return self.user.username

    def get_turning_point_str(self):
        sign = '-' if self.turning_point < 0 else ''
        tpa = abs(self.turning_point)
        return '%s%02d:%02d' % (sign, tpa / 60, tpa % 60)

    def set_turning_point_str(self, s):
        s = s.strip()
        r = re.match(r'^([+-]?)(\d+):(\d\d)$', s)
        if r is None:
            raise EWException('Invalid turning point string')
        sign, hours, minutes = r.group(1), int(r.group(2)), int(r.group(3))
        self.turning_point = ((-1 if sign == '-' else 1) *
                              (hours * 60 + minutes))

    def get_quick_labels(self):
        return unicode(self.quick_labels).split()

    @staticmethod
    def get_email_receiver_users():
        return [user
                for user in
                   (User.objects.filter(ewuser__release_emails=True).
                                 exclude(email='') |
                    User.objects.filter(ewuser=None).
                                 exclude(email=''))]


def get_ewuser(user):
    try:
        return EWUser.objects.get(pk=user)
    except EWUser.DoesNotExist, e:
        ewuser = EWUser(pk=user.pk)
        ewuser.save()
        return EWUser.objects.get(pk=user)


class WDict(models.Model):

    # WDict = word dictionary (as opposed to the dictionary data type which is
    # an "object dictionary")

    user = models.ForeignKey(User)
    name = models.CharField(max_length=255) # the name of the dictionary
    lang1 = models.CharField(max_length=255)
    lang2 = models.CharField(max_length=255)
    deleted = models.BooleanField(default=False)
    practice_word_order = models.CharField(default='default', max_length=20)

    def __unicode__(self):
        return self.name

    def get_words_to_practice_today(self, word_list_type='normal'):
        assert(word_list_type in ('normal', 'early'))
        user_time = get_user_time(user=self.user)
        today = get_today(self.user)
        result = []
        for wp in self.wordpair_set.filter(deleted=False):
            for direction in (1, 2):
                is_due = is_word_due(wp.get_date(direction), user_time)
                if word_list_type == 'normal':
                    is_needed = is_due
                else:
                    is_needed = (is_due or
                                 (wp.get_strength(direction) > 0 and
                                  wp.get_dimness(direction, today) >=
                                  MIN_DIMNESS_FOR_EARLY_PRACTICE))
                if is_needed:
                    result.append((wp, direction))
        return result

    def sort_words(self, words, order=None, word_list_type='normal'):
        # order = 'random' | 'zero_first' |
        #         ('dimness', dimness_day, dimness_direction)
        # dimness_day = 'today' | 'tomorrow'
        # dimness_direction = 'dimmer_first' | 'dimmer_last'

        # Converting `order` to the format given above
        if order is None:
            if word_list_type == 'normal':
                order = self.get_practice_word_order()
                if order in ('dimmer_first', 'dimmer_last'):
                    order = ('dimness', 'tomorrow', order)
            elif word_list_type == 'early':
                order = ('dimness', 'today', 'dimmer_first')
            else:
                unexpected_value('word_list_type', word_list_type)

        # Converting `order` to a string and possibly setting up other
        # variables
        if order in ('random', 'zero_first'):
            pass
        elif order[0] == 'dimness':
            order, dimness_day, dimness_direction = order
        else:
            unexpected_value('order', order)

        random.shuffle(words)
        if order == 'random':
            pass
        elif order in ('zero_first', 'dimness'):

            # Separating weak words (which should come first) and strong words
            # (which should come last)
            weak_words = [] # words with zero or negative strength
            strong_words = [] # words with positive strength
            for (wp, direction) in words:
                if wp.get_strength(direction) > 0:
                    strong_words.append((wp, direction))
                else:
                    weak_words.append((wp, direction))

            # Ordering the strong words by dimness
            if order == 'dimness':

                # First sort by strength
                def strength_key_fun((wp, direction)):
                    return wp.get_strength(direction)
                strong_words.sort(key=strength_key_fun)

                # Then sort by dimness
                if dimness_day == 'today':
                    dimness_day = get_today(self.user)
                elif dimness_day == 'tomorrow':
                    dimness_day = get_today(self.user) + \
                                      datetime.timedelta(days=1)
                else:
                    unexpected_value('dimness_day', dimness_day)

                def dimness_key_fun((wp, direction)):
                    return wp.get_dimness(direction, dimness_day)
                reverse = (dimness_direction == 'dimmer_first')
                strong_words.sort(key=dimness_key_fun, reverse=reverse)

            words[:] = weak_words + strong_words
        else:
            unexpected_value('order', order)

    def get_practice_word_order(self):
        if self.practice_word_order == 'default':
            return get_ewuser(self.user).practice_word_order
        else:
            return self.practice_word_order

    def get_duplicates(self, wp):
        f = WordPair.objects.filter
        lang1_same = set(f(wdict=self,
                           word_in_lang1=wp.word_in_lang1,
                           deleted=False))
        lang1_same.discard(wp)
        lang2_same = set(f(wdict=self,
                           word_in_lang2=wp.word_in_lang2,
                           deleted=False))
        lang2_same.discard(wp)
        same_word_pairs = lang1_same & lang2_same
        similar_word_pairs = (lang1_same | lang2_same) - same_word_pairs
        return sorted(same_word_pairs), sorted(similar_word_pairs)


class WordPair(models.Model):

    # each word pair belongs to a dictionary
    wdict = models.ForeignKey(WDict)

    # the word in the first/second language:
    word_in_lang1 = models.CharField(max_length=255)
    word_in_lang2 = models.CharField(max_length=255)

    # strengths of the word
    strength1 = models.FloatField(default=0)
    strength2 = models.FloatField(default=0)

    # dates of the next practice
    date_added = models.DateField()
    date1 = models.DateField()
    date2 = models.DateField()

    # explanation, examples, comments, etc.
    explanation = models.TextField(blank=True)

    # labels
    labels = models.CharField(max_length=255, blank=True)

    # whether the word pair is deleted or not
    deleted = models.BooleanField(default=False)

    def save(self):
        self.normalize()
        return models.Model.save(self)

    def normalize(self):
        self.word_in_lang1 = self.word_in_lang1.strip()
        self.word_in_lang2 = self.word_in_lang2.strip()
        self.explanation = self.explanation.rstrip()
        self.normalize_labels()

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

    def strengthen_alg1(self, direction):
        strength = self.get_strength(direction)
        today = get_today(self.wdict.user)
        new_due_interval_len = datetime.timedelta(2 ** max(strength, 0))
        self.set_strength(direction, strength + 1)
        self.set_date(direction, today + new_due_interval_len)

    def weaken_alg1(self, direction):
        self.set_date(direction, get_today(self.wdict.user))
        new_strength = min(self.get_strength(direction), 0)
        self.set_strength(direction, new_strength)

    def strengthen_alg2(self, direction, day=None, dry_run=False):

        #######################################################################
        #     Number of days before the word
        #     is asked again (i.e. length of
        #     the next "due interval")
        #                   ^                 x
        #                   |                x
        # 2 ^ strength1     + . . . . . . . X (dimness = 1 at this point)
        #                   |              x.
        #                   |             x .
        #                   |            x  .
        #                   |           x   .
        #                   |          x    .
        #                 0 +---------X-----+----------> Day on which the
        #                             ^     ^            word is practiced
        #                last_query_date  due_date
        #
        #                             <----->
        #               (previous) due_interval =  "2 ^ (strength1 - 1)" days
        #######################################################################

        #######################################################################
        # Original strength-calculating function:
        #
        #       New strength of the
        #       word (strength2)
        #                 ^
        #                 |                                 xxxxxxxxxxxxxxxxxxx
        #  strength1 + 2  +                 xxxxxxxxxxxxxxxx
        #  strength1 + 1  + . . . . Xxxxxxxx
        #      strength1  + . . Xxxx.
        #                 |   xx.   .
        #                 |  x  .   .
        #               0 +-x---+---+----------------------------------------->
        #                   ^   ^   ^                         Day on which the
        #       last_query_date | due_date                    word is practiced
        #       dimness = 0     | dimness = 1
        #                       |
        #          half-way between last_query_date and due_date
        #          dimness = 0.5
        #
        #                   <------->
        #         (previous) due_interval =  "2 ^ (strength1 - 1)" days
        #######################################################################

        #######################################################################
        # Modified strength-calculating function (strength2 should not be
        # smaller than strength1):
        #
        #       New strength of the
        #       word (strength2)
        #                 ^
        #                 |                                 xxxxxxxxxxxxxxxxxxx
        #  strength1 + 2  +                 xxxxxxxxxxxxxxxx
        #  strength1 + 1  + . . . . Xxxxxxxx
        #      strength1  + xxxxXxxx.
        #                 |     .   .
        #                 |     .   .
        #               0 +-+---+---+----------------------------------------->
        #                   ^       ^                         Day on which the
        #       last_query_date   due_date                    word is practiced
        #
        #                   <------->
        #         (previous) due_interval =  "2 ^ (strength1 - 1)" days
        #######################################################################

        #######################################################################
        #
        # Calculating due_interval2_len:
        #
        #     actual_interval_len = day - last_query_date
        #     due_interval2_len = 2 * actual_interval_len
        #
        # Calculating strength2 (original):
        #
        #     due_interval2_len = 2 ^ (strength2 - 1)      // log_2 ^ ()
        #     log_2 due_interval2_len = (strength2 - 1)    // () + 1
        #     1 + log_2 due_interval2_len = strength2
        #     strength2 = 1 + log_2 due_interval2_len
        #
        # Calculating strength2 (modified):
        #
        #     strength2 = max(1 + log_2 due_interval2_len, strength1)
        #
        #######################################################################

        if day is None:
            day = get_today(self.wdict.user)

        strength1 = self.get_strength(direction)
        if strength1 <= 0:
            # if the word is new, ask tomorrow
            strength2 = strength1 + 1
            date2 = day + datetime.timedelta(days=1)
        else:
            last_query_date, due_date, due_interval_len = \
                self.get_date_info(direction)
            actual_interval_len = (day - last_query_date).days
            if due_interval_len <= 0:
                # if the word was already strengthened today, don't change
                # anything
                strength2 = strength1
                date2 = date1
            else:
                # otherwise use the nice equasion
                due_interval2_len = 2 * actual_interval_len
                strength2 = max(1 + math.log(due_interval2_len, 2), strength1)
                date2 = day + datetime.timedelta(days=due_interval2_len)

        if not dry_run:
            self.set_strength(direction, strength2)
            self.set_date(direction, date2)

        return strength2, date2

    def weaken_alg2(self, direction, day=None):
        if day is None:
            day = get_today(self.wdict.user)
        self.set_date(direction, day)
        new_strength = min(self.get_strength(direction), 0)
        self.set_strength(direction, new_strength)

    def strengthen(self, direction):
        if self.wdict.user == 'hcs':
            self.strengthen_alg2(direction)
        else:
            self.strengthen_alg1(direction)

    def weaken(self, direction):
        if self.wdict.user == 'hcs':
            self.weaken_alg2(direction)
        else:
            self.weaken_alg1(direction)

    def get_date_info(self, direction):
        due_date = self.get_date(direction)
        due_interval = int(round(2 ** (self.get_strength(direction) - 1)))
        last_query_date = (due_date - datetime.timedelta(days=due_interval))
        return last_query_date, due_date, due_interval

    def get_dimness(self, direction, day, silent=False):

        # The dimness function does not have a value when strength = 0.
        # (Mathematically, it would have the value of 0, but in ExponWords,
        # strength = 0 means is a special value meaning that the word
        # definitely needs practice, and 0 dimness would mean that it does not
        # need a practice.)
        #
        # The dimness function looks like this when strength > 0:
        #
        # dimness
        #   ^                 x
        #   |                x
        # 1 + . . . . . . . X
        #   |              x.
        #   |             x .
        #   |            x  .
        #   |           x   .
        #   |          x    .
        # 0 +---------X-----+----------> day
        #             ^     ^
        # last_query_date  due_date
        #
        #             <----->
        #          due_interval =  "2 ^ (strength - 1)" days

        strength = self.get_strength(direction)
        if silent and strength == 0:
            return None
        assert(strength > 0)

        last_query_date, due_date, due_interval = self.get_date_info(direction)
        return float((day - last_query_date).days) / due_interval

    @staticmethod
    def get_label_set_from_str(s):
        return set(unicode(s).split())

    def get_label_set(self):
        return self.get_label_set_from_str(self.labels)

    def set_label_set(self, label_set):
        self.labels = ' '.join(sorted(label_set))

    def normalize_labels(self):
        self.set_label_set(self.get_label_set())

    def add_labels(self, labels):
        self.set_label_set(self.get_label_set() |
                           self.get_label_set_from_str(labels))

    def remove_labels(self, labels):
        self.set_label_set(self.get_label_set() -
                           self.get_label_set_from_str(labels))

    def set_labels(self, labels):
        self.set_label_set(self.get_label_set_from_str(labels))

    @staticmethod
    def get_simple_fields():
        return ('word_in_lang1',
                'word_in_lang2',
                'explanation')

    @staticmethod
    def get_advanced_fields():
        return ('labels',
                'date_added',
                'date1',
                'date2',
                'strength1',
                'strength2')

    @staticmethod
    # fields_to_be_edited = simple_fields + advanced_fields
    def get_fields_to_be_edited():
        return ('word_in_lang1',
                'word_in_lang2',
                'explanation',
                'labels',
                'date_added',
                'date1',
                'date2',
                'strength1',
                'strength2')

    @staticmethod
    # Get the list of fields whose value should be saved when adding a word
    # pair, and reused when another word pair is added
    def get_fields_to_be_saved():
        return ('labels',
                'date1',
                'date2',
                'strength1',
                'strength2')

    def get_saved_fields(self):
        saved_fields = {}
        for field in self.get_fields_to_be_saved():
            saved_fields[field] = getattr(self, field)
        return saved_fields

    @staticmethod
    def prefix(s, max_length):
        if len(s) <= max_length:
            return s
        else:
            return s[:max_length - 3] + '...'

    def get_short_repr(self):
        return (self.prefix(self.word_in_lang1, WORD_PREFIX) +
                ' / ' +
                self.prefix(self.word_in_lang2, WORD_PREFIX))


##### Importing and exporting word pairs #####


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

    user = wdict.user
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
                wp.date_added = get_today(user)
                wp.date1 = datetime.date(int(r.group(7)),
                                         int(r.group(8)),
                                         int(r.group(9)))
                wp.date2 = datetime.date(int(r.group(11)),
                                         int(r.group(12)),
                                         int(r.group(13)))
                wp.strength1 = int(r.group(6))
                wp.strength2 = int(r.group(10))
            else:
                wp.date_added = get_today(user)
                wp.date1 = get_today(user)
                wp.date2 = get_today(user)
                wp.strength1 = 0
                wp.strength2 = 0

        i += 1

    create_add_word_pairs(wdict, word_pairs)
    return word_pairs


def import_tsv(s, wdict):
    """Adds words from a text of tab-separeted values to a dictionary.

    Arguments:
    - s (str)
    - wdict (WDict)
    """

    user = wdict.user
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
            wp.date1 = get_today(user)
            wp.date2 = get_today(user)
            wp.date_added = get_today(user)
            word_pairs.append(wp)
        else:
            msg = (_('Too many fields in line %(linenumber)s: %(line)s') %
                   {'linenumber': i, 'line': line})
            raise EWException(msg)

        i += 1

    create_add_word_pairs(wdict, word_pairs)
    return word_pairs


def export_textfile(wdict=None, word_pairs=None):
    """Prints a dictionary in the old text format.

    Arguments:
    - wdict (WDict)

    Returns: str
    """

    if wdict is None and word_pairs is None:
        raise EWException('export_textfile: Either the wdict or the word_pairs '
                          'parameter has to be not None')
    elif wdict is not None:
        word_pairs = wdict.wordpair_set.filter(deleted=False)

    result = []
    for wp in word_pairs:
        result.append(
            '%s -- %s <%s %s><%s %s>\n' %
            (wp.word_in_lang1.replace('\n', ' ').replace('\r', ' '),
             wp.word_in_lang2.replace('\n', ' ').replace('\r', ' '),
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


##### Logging #####


class EWLogEntry(models.Model):

    datetime = models.DateTimeField()
    action = models.TextField()
    user = models.ForeignKey(User, blank=True, null=True)
    username = models.TextField(blank=True)
    text = models.TextField(blank=True)
    ipaddress = models.TextField(blank=True)

    def __unicode__(self):
        return ('%s <%s> %s | %s' %
                (self.datetime.strftime('%Y-%m-%d %H-%M-%S'), self.username,
                 self.action, self.text))


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


##### Announcing releases #####

class Announcement(models.Model):

    lang = models.CharField(max_length=10, primary_key=True)
    text = models.TextField()

    def __unicode__(self):
        return self.lang + ' | ' + self.text.splitlines()[0]


##### Show the future #####


def incr_wcd(wcd, wdict, strength, date, count):
    strength_to_word_count = wcd.setdefault((wdict, date), {})
    try:
        strength_to_word_count[strength] += count
    except KeyError:
        strength_to_word_count[strength] = count


def get_initial_word_counts_dict(user, start_date):
    """
    Returns: wdicts, {(wdict, date): {strength: word_count}}
    """

    def add_wp(wcd, wdict, strength, date):
        if (start_date is not None) and (date < start_date):
            date = start_date
        incr_wcd(wcd, wdict, strength, date, 1)

    wcd = {}
    wdicts = WDict.objects.filter(user=user, deleted=False)
    word_pairs = WordPair.objects.filter(wdict__user=user,
                                         wdict__deleted=False,
                                         deleted=False)
    for wp in word_pairs:
        add_wp(wcd, wp.wdict, wp.strength1, wp.date1)
        add_wp(wcd, wp.wdict, wp.strength2, wp.date2)
    return wdicts, wcd


def calc_future(user, days_count, start_date):
    """
    Returns: [date], [WDict], {(WDict, date): question_count}
    """

    dates = [start_date + datetime.timedelta(i)
             for i in range(days_count)]

    wdicts, wcd = get_initial_word_counts_dict(user, start_date)

    date_to_question_count = {} # {(wdict, date): question_count}
    for date in dates:
        for wdict in wdicts:
            strength_to_word_count = wcd.pop((wdict, date), {})
            question_count = 0
            for strength, word_count in strength_to_word_count.items():
                question_count += word_count
                today = get_today(user)
                new_date = today + datetime.timedelta(2 ** max(strength, 0))
                incr_wcd(wcd, wdict, strength + 1, new_date, word_count)
            date_to_question_count[(wdict, date)] = question_count

    return dates, wdicts, date_to_question_count


##### Miscellaneous utilities #####


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

    def __str__(self):
        return self.__unicode__()


def get_labels(user):
    all_word_pairs = WordPair.objects.filter(wdict__user=user,
                                             wdict__deleted=False,
                                             deleted=False)
    labels = set()
    for wp in all_word_pairs:
        labels.update(unicode(wp.labels).split())
    return labels


def parse_date(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d')
